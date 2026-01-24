"""
Neo4j Database Service

Handles connection pooling and query execution for the API.
"""

import os
from contextlib import contextmanager
from typing import Optional, Generator
from neo4j import GraphDatabase, Driver, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required")


class Neo4jService:
    """Singleton service for Neo4j database operations."""

    _instance: Optional["Neo4jService"] = None
    _driver: Optional[Driver] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

    @property
    def driver(self) -> Driver:
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Check if database is reachable."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """Execute a query and return results as list of dicts."""
        with self.get_session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_single(self, query: str, parameters: dict = None) -> Optional[dict]:
        """Execute a query and return single result or None."""
        with self.get_session() as session:
            result = session.run(query, parameters or {}).single()
            return result.data() if result else None


# Global service instance
_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """Get or create the Neo4j service instance."""
    global _service
    if _service is None:
        _service = Neo4jService()
    return _service


def close_neo4j_service():
    """Close the Neo4j service connection."""
    global _service
    if _service:
        _service.close()
        _service = None


# Dependency injection for FastAPI
def get_db() -> Generator[Neo4jService, None, None]:
    """FastAPI dependency for database access."""
    service = get_neo4j_service()
    try:
        yield service
    finally:
        pass  # Connection pooling handles cleanup


# Query helpers
class IngredientQueries:
    """Cypher queries for ingredient operations."""

    LIST_INGREDIENTS = """
        MATCH (i:Ingredient)
        WHERE $category IS NULL OR i.category = $category
        RETURN i.id as id, i.name as name,
               i.category as category, i.subcategory as subcategory
        ORDER BY i.name
        SKIP $skip
        LIMIT $limit
    """

    SEARCH_INGREDIENTS = """
        CALL db.index.fulltext.queryNodes('ingredient_search', $search + '*')
        YIELD node, score
        RETURN node.id as id, node.name as name,
               node.category as category, node.subcategory as subcategory,
               score
        ORDER BY score DESC
        LIMIT $limit
    """

    GET_INGREDIENT = """
        MATCH (i:Ingredient {id: $id})
        RETURN i.id as id, i.name as name,
               i.category as category, i.subcategory as subcategory,
               i.aliases as aliases
    """

    GET_INGREDIENT_COMPOUNDS = """
        MATCH (i:Ingredient {id: $id})-[r:CONTAINS]->(c:FlavorCompound)
        RETURN c.id as id, c.name as name, c.common_name as common_name,
               c.odor_description as odor_description,
               r.concentration as concentration
        ORDER BY r.concentration DESC
    """

    GET_PAIRINGS = """
        MATCH (i:Ingredient {id: $id})-[p:PAIRS_WITH]->(other:Ingredient)
        WHERE p.score >= $min_score
        RETURN other.id as id, other.name as name, other.category as category,
               p.score as score, p.shared_compounds as shared_compounds,
               p.key_compounds as key_compounds, p.explanation as explanation
        ORDER BY p.score DESC
        LIMIT $limit
    """

    COMPARE_INGREDIENTS = """
        MATCH (i1:Ingredient {id: $id1})-[r1:CONTAINS]->(c:FlavorCompound)<-[r2:CONTAINS]-(i2:Ingredient {id: $id2})
        RETURN c.id as id, c.name as name, c.common_name as common_name,
               c.odor_description as odor_description,
               r1.concentration as concentration_1,
               r2.concentration as concentration_2
        ORDER BY (r1.concentration + r2.concentration) DESC
    """

    GET_PAIRING_SCORE = """
        MATCH (i1:Ingredient {id: $id1})-[p:PAIRS_WITH]-(i2:Ingredient {id: $id2})
        RETURN p.score as score, p.shared_compounds as shared_compounds,
               p.key_compounds as key_compounds, p.explanation as explanation
        LIMIT 1
    """


class CompoundQueries:
    """Cypher queries for compound operations."""

    GET_COMPOUND = """
        MATCH (c:FlavorCompound {id: $id})
        RETURN c.id as id, c.name as name, c.common_name as common_name,
               c.formula as formula, c.odor_description as odor_description,
               c.taste_profiles as taste_profiles
    """

    GET_COMPOUND_INGREDIENTS = """
        MATCH (c:FlavorCompound {id: $id})<-[r:CONTAINS]-(i:Ingredient)
        RETURN i.id as id, i.name as name, i.category as category,
               r.concentration as concentration
        ORDER BY r.concentration DESC
        LIMIT $limit
    """

    LIST_COMPOUNDS = """
        MATCH (c:FlavorCompound)
        RETURN c.id as id, c.name as name, c.common_name as common_name
        ORDER BY c.name
        SKIP $skip
        LIMIT $limit
    """


class ExploreQueries:
    """Cypher queries for graph exploration."""

    GET_CATEGORIES = """
        MATCH (c:Category)<-[:BELONGS_TO]-(i:Ingredient)
        RETURN c.id as id, c.name as name, count(i) as count
        ORDER BY count DESC
    """

    GET_TASTE_PROFILES = """
        MATCH (t:TasteProfile)
        OPTIONAL MATCH (t)<-[:HAS_PROFILE]-(c:FlavorCompound)
        RETURN t.id as id, t.name as name, t.description as description,
               count(c) as compound_count
        ORDER BY compound_count DESC
    """

    SURPRISE_PAIRINGS = """
        MATCH (i1:Ingredient)-[p:PAIRS_WITH]->(i2:Ingredient)
        WHERE i1.category <> i2.category AND p.score > $min_score
        RETURN i1.id as id1, i1.name as name1, i1.category as category1,
               i2.id as id2, i2.name as name2, i2.category as category2,
               p.score as score, p.key_compounds as key_compounds,
               p.explanation as explanation
        ORDER BY p.score DESC
        LIMIT $limit
    """

    EXPLORE_GRAPH = """
        MATCH (center:Ingredient {id: $center})
        OPTIONAL MATCH (center)-[p:PAIRS_WITH]-(neighbor:Ingredient)
        WHERE p.score >= $min_score
        WITH center, collect(DISTINCT {
            node: neighbor,
            score: p.score
        })[0..$limit] as neighbors
        RETURN center, neighbors
    """

    GET_STATS = """
        MATCH (i:Ingredient) WITH count(i) as ingredients
        MATCH (c:FlavorCompound) WITH ingredients, count(c) as compounds
        MATCH ()-[r:CONTAINS]->() WITH ingredients, compounds, count(r) as contains
        MATCH ()-[p:PAIRS_WITH]->() WITH ingredients, compounds, contains, count(p) as pairings
        RETURN ingredients, compounds, contains, pairings / 2 as pairings
    """
