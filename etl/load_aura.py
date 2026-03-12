"""
Neo4j Aura Data Loading Script

Loads data into Neo4j Aura using direct Cypher statements (not LOAD CSV).
Neo4j Aura doesn't support LOAD CSV from local files, so we read CSVs
locally and batch-insert using UNWIND.
"""

import os
import csv
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
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", None)
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required")

# CSV directory
NEO4J_DIR = Path(__file__).parent.parent / "data" / "neo4j"

# Batch size for inserts
BATCH_SIZE = 500


class Neo4jAuraLoader:
    """Handles loading data into Neo4j Aura."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """Execute a Cypher query and return results."""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        logger.warning("Clearing all data from database...")
        # Delete in batches to avoid memory issues
        while True:
            result = self.execute_query("""
                MATCH (n)
                WITH n LIMIT 10000
                DETACH DELETE n
                RETURN count(*) as deleted
            """)
            deleted = result[0]['deleted'] if result else 0
            if deleted == 0:
                break
            logger.info(f"Deleted {deleted} nodes...")
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

    def read_csv(self, filename: str) -> list:
        """Read a CSV file and return list of dictionaries."""
        filepath = NEO4J_DIR / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def batch_insert(self, data: list, query: str, batch_size: int = BATCH_SIZE) -> int:
        """Insert data in batches using UNWIND."""
        total = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            result = self.execute_query(query, {"batch": batch})
            count = result[0]['count'] if result else 0
            total += count
        return total

    def load_ingredients(self):
        """Load ingredients."""
        logger.info("Loading ingredients...")
        data = self.read_csv("ingredients.csv")

        query = """
        UNWIND $batch AS row
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

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} ingredients")
        return count

    def load_compounds(self):
        """Load flavor compounds."""
        logger.info("Loading compounds...")
        data = self.read_csv("compounds.csv")

        query = """
        UNWIND $batch AS row
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

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} compounds")
        return count

    def load_categories(self):
        """Load categories."""
        logger.info("Loading categories...")
        data = self.read_csv("categories.csv")

        query = """
        UNWIND $batch AS row
        CREATE (c:Category {
            id: row.id,
            name: row.name,
            parent_id: COALESCE(row.parent_id, '')
        })
        RETURN count(c) as count
        """

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} categories")
        return count

    def load_taste_profiles(self):
        """Load taste profiles."""
        logger.info("Loading taste profiles...")
        data = self.read_csv("taste_profiles.csv")

        query = """
        UNWIND $batch AS row
        CREATE (t:TasteProfile {
            id: row.id,
            name: row.name,
            description: COALESCE(row.description, '')
        })
        RETURN count(t) as count
        """

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} taste profiles")
        return count

    def load_contains_relationships(self):
        """Load CONTAINS relationships (ingredient -> compound)."""
        logger.info("Loading CONTAINS relationships...")
        data = self.read_csv("contains.csv")

        query = """
        UNWIND $batch AS row
        MATCH (i:Ingredient {id: row.ingredient_id})
        MATCH (c:FlavorCompound {id: row.compound_id})
        CREATE (i)-[:CONTAINS {
            concentration: toFloat(row.concentration),
            source: COALESCE(row.source, 'flavordb')
        }]->(c)
        RETURN count(*) as count
        """

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} CONTAINS relationships")
        return count

    def load_belongs_to_relationships(self):
        """Load BELONGS_TO relationships (ingredient -> category)."""
        logger.info("Loading BELONGS_TO relationships...")
        data = self.read_csv("belongs_to.csv")

        query = """
        UNWIND $batch AS row
        MATCH (i:Ingredient {id: row.ingredient_id})
        MATCH (c:Category {id: row.category_id})
        CREATE (i)-[:BELONGS_TO]->(c)
        RETURN count(*) as count
        """

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} BELONGS_TO relationships")
        return count

    def load_has_profile_relationships(self):
        """Load HAS_PROFILE relationships (compound -> taste profile)."""
        logger.info("Loading HAS_PROFILE relationships...")
        data = self.read_csv("has_profile.csv")

        query = """
        UNWIND $batch AS row
        MATCH (c:FlavorCompound {id: row.compound_id})
        MATCH (t:TasteProfile {id: row.taste_profile_id})
        CREATE (c)-[:HAS_PROFILE {
            intensity: toFloat(row.intensity)
        }]->(t)
        RETURN count(*) as count
        """

        count = self.batch_insert(data, query)
        logger.info(f"Loaded {count} HAS_PROFILE relationships")
        return count

    def load_pairs_with_relationships(self):
        """Load PAIRS_WITH relationships (ingredient -> ingredient)."""
        logger.info("Loading PAIRS_WITH relationships...")
        data = self.read_csv("pairs_with.csv")

        query = """
        UNWIND $batch AS row
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

        count = self.batch_insert(data, query)
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


def load_all(clear_first: bool = True):
    """Load all data into Neo4j Aura."""

    loader = Neo4jAuraLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Optionally clear existing data
        if clear_first:
            loader.clear_database()

        # Create constraints and indexes
        loader.create_constraints_and_indexes()

        # Load nodes
        loader.load_ingredients()
        loader.load_compounds()
        loader.load_categories()
        loader.load_taste_profiles()

        # Load relationships
        loader.load_contains_relationships()
        loader.load_belongs_to_relationships()
        loader.load_has_profile_relationships()
        loader.load_pairs_with_relationships()

        # Note: reverse pairings skipped - API uses undirected queries
        # instead, to stay within Aura free tier relationship limits

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load data into Neo4j Aura")
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing data before loading"
    )

    args = parser.parse_args()
    load_all(clear_first=not args.no_clear)
