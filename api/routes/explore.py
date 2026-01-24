"""
Graph Exploration API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..services.neo4j_service import (
    Neo4jService,
    get_db,
    ExploreQueries as Q,
    IngredientQueries
)
from ..models.schemas import (
    Category,
    TasteProfile,
    GraphData,
    GraphNode,
    GraphLink,
    SurprisePairing,
    IngredientBase,
    DatabaseStats,
)

router = APIRouter(prefix="/explore", tags=["explore"])

# Rate limiter (shared with main app)
limiter = Limiter(key_func=get_remote_address)


@router.get("/categories", response_model=list[Category])
@limiter.limit("30/minute")
def list_categories(
    request: Request,
    db: Neo4jService = Depends(get_db)
):
    """
    List all ingredient categories with counts.

    Returns categories sorted by ingredient count (most first).
    """
    results = db.execute_query(Q.GET_CATEGORIES)
    return [Category(**r) for r in results]


@router.get("/taste-profiles", response_model=list[TasteProfile])
@limiter.limit("30/minute")
def list_taste_profiles(
    request: Request,
    db: Neo4jService = Depends(get_db)
):
    """
    List all taste profiles (sweet, sour, bitter, salty, umami).
    """
    results = db.execute_query(Q.GET_TASTE_PROFILES)
    return [TasteProfile(**r) for r in results]


@router.get("/surprise", response_model=list[SurprisePairing])
@limiter.limit("30/minute")
def get_surprise_pairings(
    request: Request,
    min_score: float = Query(0.6, ge=0, le=1, description="Minimum pairing score"),
    limit: int = Query(10, ge=1, le=50, description="Maximum pairings to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    Get unexpected but highly-rated pairings.

    Returns pairings where ingredients are from different categories
    but have a high pairing score based on shared compounds.
    """
    results = db.execute_query(
        Q.SURPRISE_PAIRINGS,
        {"min_score": min_score, "limit": limit}
    )

    pairings = []
    for r in results:
        pairings.append(SurprisePairing(
            ingredient_1=IngredientBase(
                id=r["id1"],
                name=r["name1"],
                category=r["category1"],
                subcategory=""
            ),
            ingredient_2=IngredientBase(
                id=r["id2"],
                name=r["name2"],
                category=r["category2"],
                subcategory=""
            ),
            score=r["score"],
            key_compounds=r.get("key_compounds", []),
            explanation=r.get("explanation", ""),
        ))

    return pairings


@router.get("/graph", response_model=GraphData)
@limiter.limit("30/minute")
def get_graph_data(
    request: Request,
    center: str = Query(..., description="Center ingredient ID"),
    min_score: float = Query(0.4, ge=0, le=1, description="Minimum pairing score"),
    limit: int = Query(20, ge=1, le=50, description="Maximum neighbors to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    Get graph data for visualization centered on an ingredient.

    Returns nodes and links for a force-directed graph visualization.
    The center ingredient and its top pairings are included.
    """
    # Verify center ingredient exists
    center_ing = db.execute_single(
        IngredientQueries.GET_INGREDIENT,
        {"id": center}
    )
    if not center_ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    # Get neighbors (pairings)
    result = db.execute_single(
        Q.EXPLORE_GRAPH,
        {"center": center, "min_score": min_score, "limit": limit}
    )

    # Build nodes list
    nodes = [
        GraphNode(
            id=center_ing["id"],
            name=center_ing["name"],
            category=center_ing["category"],
            type="ingredient"
        )
    ]

    links = []

    if result and result.get("neighbors"):
        for neighbor_data in result["neighbors"]:
            if neighbor_data.get("node"):
                neighbor = neighbor_data["node"]
                score = neighbor_data.get("score", 0)

                nodes.append(GraphNode(
                    id=neighbor["id"],
                    name=neighbor["name"],
                    category=neighbor.get("category"),
                    type="ingredient"
                ))

                links.append(GraphLink(
                    source=center,
                    target=neighbor["id"],
                    score=score,
                    type="pairs_with"
                ))

    return GraphData(nodes=nodes, links=links)


@router.get("/stats", response_model=DatabaseStats)
@limiter.limit("30/minute")
def get_database_stats(
    request: Request,
    db: Neo4jService = Depends(get_db)
):
    """
    Get database statistics.

    Returns counts of ingredients, compounds, and relationships.
    """
    result = db.execute_single(Q.GET_STATS)

    if not result:
        return DatabaseStats(
            ingredients=0,
            compounds=0,
            contains_relationships=0,
            pairings=0
        )

    return DatabaseStats(
        ingredients=result.get("ingredients", 0),
        compounds=result.get("compounds", 0),
        contains_relationships=result.get("contains", 0),
        pairings=result.get("pairings", 0)
    )


@router.get("/random", response_model=IngredientBase)
@limiter.limit("30/minute")
def get_random_ingredient(
    request: Request,
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: Neo4jService = Depends(get_db)
):
    """
    Get a random ingredient.

    Useful for "I'm feeling lucky" or inspiration features.
    """
    if category:
        query = """
            MATCH (i:Ingredient {category: $category})
            WITH i, rand() as r
            ORDER BY r
            LIMIT 1
            RETURN i.id as id, i.name as name,
                   i.category as category, i.subcategory as subcategory
        """
        result = db.execute_single(query, {"category": category})
    else:
        query = """
            MATCH (i:Ingredient)
            WITH i, rand() as r
            ORDER BY r
            LIMIT 1
            RETURN i.id as id, i.name as name,
                   i.category as category, i.subcategory as subcategory
        """
        result = db.execute_single(query)

    if not result:
        raise HTTPException(status_code=404, detail="No ingredients found")

    return IngredientBase(**result)
