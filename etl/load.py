"""
Neo4j Data Loading Script

Loads CSV data into Neo4j graph database.
Requires Neo4j to be running (docker-compose up neo4j).
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required")

# CSV directory (relative to Neo4j import directory)
# When using Docker, files in data/neo4j are mounted to /import
CSV_IMPORT_PREFIX = "file:///"  # For local Neo4j
NEO4J_DIR = Path(__file__).parent.parent / "data" / "neo4j"


class Neo4jLoader:
    """Handles loading data into Neo4j."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        logger.warning("Clearing all data from database...")
        self.execute_query("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")

    def create_constraints_and_indexes(self):
        """Create constraints and indexes for performance."""
        logger.info("Creating constraints and indexes...")

        constraints = [
            "CREATE CONSTRAINT ingredient_id IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (c:FlavorCompound) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT taste_profile_id IF NOT EXISTS FOR (t:TasteProfile) REQUIRE t.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX ingredient_name IF NOT EXISTS FOR (i:Ingredient) ON (i.name)",
            "CREATE INDEX ingredient_category IF NOT EXISTS FOR (i:Ingredient) ON (i.category)",
            "CREATE INDEX compound_name IF NOT EXISTS FOR (c:FlavorCompound) ON (c.name)",
        ]

        for constraint in constraints:
            try:
                self.execute_query(constraint)
                logger.info(f"Created: {constraint.split('FOR')[0].strip()}")
            except Exception as e:
                logger.debug(f"Constraint may already exist: {e}")

        for index in indexes:
            try:
                self.execute_query(index)
                logger.info(f"Created: {index.split('FOR')[0].strip()}")
            except Exception as e:
                logger.debug(f"Index may already exist: {e}")

        # Create fulltext index for search
        try:
            self.execute_query("""
                CREATE FULLTEXT INDEX ingredient_search IF NOT EXISTS
                FOR (i:Ingredient) ON EACH [i.name, i.aliases]
            """)
            logger.info("Created fulltext index for ingredient search")
        except Exception as e:
            logger.debug(f"Fulltext index may already exist: {e}")

    def load_ingredients(self, csv_path: str):
        """Load ingredients from CSV."""
        logger.info("Loading ingredients...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        CREATE (i:Ingredient {
            id: row.id,
            name: row.name,
            category: row.category,
            subcategory: COALESCE(row.subcategory, ''),
            aliases: CASE WHEN row.aliases IS NOT NULL AND row.aliases <> ''
                         THEN split(row.aliases, ';')
                         ELSE [] END
        })
        RETURN count(i) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} ingredients")
        return count

    def load_compounds(self, csv_path: str):
        """Load flavor compounds from CSV."""
        logger.info("Loading compounds...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        CREATE (c:FlavorCompound {
            id: row.id,
            name: row.name,
            common_name: COALESCE(row.common_name, ''),
            formula: COALESCE(row.formula, ''),
            odor_description: COALESCE(row.odor_description, ''),
            taste_profiles: CASE WHEN row.taste_profiles IS NOT NULL AND row.taste_profiles <> ''
                                THEN split(row.taste_profiles, ';')
                                ELSE [] END
        })
        RETURN count(c) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} compounds")
        return count

    def load_categories(self, csv_path: str):
        """Load categories from CSV."""
        logger.info("Loading categories...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        CREATE (c:Category {
            id: row.id,
            name: row.name,
            parent_id: COALESCE(row.parent_id, '')
        })
        RETURN count(c) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} categories")
        return count

    def load_taste_profiles(self, csv_path: str):
        """Load taste profiles from CSV."""
        logger.info("Loading taste profiles...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        CREATE (t:TasteProfile {
            id: row.id,
            name: row.name,
            description: COALESCE(row.description, '')
        })
        RETURN count(t) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} taste profiles")
        return count

    def load_contains_relationships(self, csv_path: str):
        """Load CONTAINS relationships (ingredient -> compound)."""
        logger.info("Loading CONTAINS relationships...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        MATCH (i:Ingredient {id: row.ingredient_id})
        MATCH (c:FlavorCompound {id: row.compound_id})
        CREATE (i)-[:CONTAINS {
            concentration: toFloat(row.concentration),
            source: COALESCE(row.source, 'flavordb')
        }]->(c)
        RETURN count(*) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} CONTAINS relationships")
        return count

    def load_belongs_to_relationships(self, csv_path: str):
        """Load BELONGS_TO relationships (ingredient -> category)."""
        logger.info("Loading BELONGS_TO relationships...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        MATCH (i:Ingredient {id: row.ingredient_id})
        MATCH (c:Category {id: row.category_id})
        CREATE (i)-[:BELONGS_TO]->(c)
        RETURN count(*) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} BELONGS_TO relationships")
        return count

    def load_has_profile_relationships(self, csv_path: str):
        """Load HAS_PROFILE relationships (compound -> taste profile)."""
        logger.info("Loading HAS_PROFILE relationships...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        MATCH (c:FlavorCompound {id: row.compound_id})
        MATCH (t:TasteProfile {id: row.taste_profile_id})
        CREATE (c)-[:HAS_PROFILE {
            intensity: toFloat(row.intensity)
        }]->(t)
        RETURN count(*) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} HAS_PROFILE relationships")
        return count

    def load_pairs_with_relationships(self, csv_path: str):
        """Load PAIRS_WITH relationships (ingredient -> ingredient)."""
        logger.info("Loading PAIRS_WITH relationships...")

        query = """
        LOAD CSV WITH HEADERS FROM $csv_path AS row
        MATCH (a:Ingredient {id: row.ingredient_a})
        MATCH (b:Ingredient {id: row.ingredient_b})
        CREATE (a)-[:PAIRS_WITH {
            score: toFloat(row.score),
            shared_compounds: toInteger(row.shared_compounds),
            key_compounds: CASE WHEN row.key_compounds IS NOT NULL AND row.key_compounds <> ''
                               THEN split(row.key_compounds, ';')
                               ELSE [] END,
            explanation: COALESCE(row.explanation, '')
        }]->(b)
        RETURN count(*) as count
        """

        result = self.execute_query(query, {"csv_path": csv_path})
        count = result[0]['count'] if result else 0
        logger.info(f"Loaded {count} PAIRS_WITH relationships")
        return count

    def create_reverse_pairings(self):
        """Create reverse PAIRS_WITH relationships for bidirectional queries."""
        logger.info("Creating reverse pairing relationships...")

        query = """
        MATCH (a:Ingredient)-[p:PAIRS_WITH]->(b:Ingredient)
        WHERE NOT EXISTS((b)-[:PAIRS_WITH]->(a))
        CREATE (b)-[:PAIRS_WITH {
            score: p.score,
            shared_compounds: p.shared_compounds,
            key_compounds: p.key_compounds,
            explanation: p.explanation
        }]->(a)
        RETURN count(*) as count
        """

        result = self.execute_query(query)
        count = result[0]['count'] if result else 0
        logger.info(f"Created {count} reverse pairing relationships")
        return count

    def verify_load(self):
        """Verify data was loaded correctly."""
        logger.info("Verifying loaded data...")

        counts = {}

        # Count nodes
        for label in ['Ingredient', 'FlavorCompound', 'Category', 'TasteProfile']:
            result = self.execute_query(f"MATCH (n:{label}) RETURN count(n) as count")
            counts[label] = result[0]['count'] if result else 0

        # Count relationships
        for rel_type in ['CONTAINS', 'BELONGS_TO', 'HAS_PROFILE', 'PAIRS_WITH']:
            result = self.execute_query(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
            counts[rel_type] = result[0]['count'] if result else 0

        return counts


def get_csv_path(filename: str) -> str:
    """Get the full path for a CSV file for LOAD CSV.

    When Neo4j runs in Docker with ./data/neo4j mounted to /import,
    just use the filename since server.directories.import=/import.
    """
    # For Docker Neo4j with import directory configured,
    # just use the filename (Neo4j will look in /import/)
    return f"file:///{filename}"


def load_all(clear_first: bool = True):
    """Load all data into Neo4j."""

    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Optionally clear existing data
        if clear_first:
            loader.clear_database()

        # Create constraints and indexes
        loader.create_constraints_and_indexes()

        # Load nodes
        loader.load_ingredients(get_csv_path("ingredients.csv"))
        loader.load_compounds(get_csv_path("compounds.csv"))
        loader.load_categories(get_csv_path("categories.csv"))
        loader.load_taste_profiles(get_csv_path("taste_profiles.csv"))

        # Load relationships
        loader.load_contains_relationships(get_csv_path("contains.csv"))
        loader.load_belongs_to_relationships(get_csv_path("belongs_to.csv"))
        loader.load_has_profile_relationships(get_csv_path("has_profile.csv"))
        loader.load_pairs_with_relationships(get_csv_path("pairs_with.csv"))

        # Create reverse pairings for bidirectional queries
        loader.create_reverse_pairings()

        # Verify
        counts = loader.verify_load()

        print("\n=== Load Summary ===")
        print("Nodes:")
        for label in ['Ingredient', 'FlavorCompound', 'Category', 'TasteProfile']:
            print(f"  {label}: {counts.get(label, 0)}")
        print("\nRelationships:")
        for rel_type in ['CONTAINS', 'BELONGS_TO', 'HAS_PROFILE', 'PAIRS_WITH']:
            print(f"  {rel_type}: {counts.get(rel_type, 0)}")

        logger.info("Data loading complete!")

    finally:
        loader.close()


def test_queries():
    """Run some test queries to verify the graph."""

    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        print("\n=== Test Queries ===\n")

        # Query 1: Get sample ingredients
        print("1. Sample Ingredients:")
        result = loader.execute_query("""
            MATCH (i:Ingredient)
            RETURN i.name as name, i.category as category
            LIMIT 5
        """)
        for r in result:
            print(f"   {r['name']} ({r['category']})")

        # Query 2: Get top pairings
        print("\n2. Top Pairings:")
        result = loader.execute_query("""
            MATCH (a:Ingredient)-[p:PAIRS_WITH]->(b:Ingredient)
            RETURN a.name as ing1, b.name as ing2, p.score as score
            ORDER BY p.score DESC
            LIMIT 5
        """)
        for r in result:
            print(f"   {r['ing1']} + {r['ing2']}: {r['score']:.2f}")

        # Query 3: Get ingredient with compounds
        print("\n3. Sample Ingredient Compounds:")
        result = loader.execute_query("""
            MATCH (i:Ingredient)-[r:CONTAINS]->(c:FlavorCompound)
            RETURN i.name as ingredient, c.name as compound, r.concentration as conc
            LIMIT 5
        """)
        for r in result:
            print(f"   {r['ingredient']} contains {r['compound']} ({r['conc']:.2f})")

        # Query 4: Categories
        print("\n4. Categories:")
        result = loader.execute_query("""
            MATCH (c:Category)<-[:BELONGS_TO]-(i:Ingredient)
            RETURN c.name as category, count(i) as count
            ORDER BY count DESC
            LIMIT 5
        """)
        for r in result:
            print(f"   {r['category']}: {r['count']} ingredients")

    finally:
        loader.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load data into Neo4j")
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing data before loading"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test queries after loading"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only run test queries (don't load data)"
    )

    args = parser.parse_args()

    if args.test_only:
        test_queries()
    else:
        load_all(clear_first=not args.no_clear)
        if args.test:
            test_queries()
