"""
Ingredient API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..services.neo4j_service import (
    Neo4jService,
    get_db,
    IngredientQueries as Q
)
from ..models.schemas import (
    IngredientBase,
    IngredientDetail,
    CompoundInIngredient,
    Pairing,
    SharedCompound,
    ComparisonResult,
)

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

# Rate limiter (shared with main app)
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=list[IngredientBase])
@limiter.limit("30/minute")
def list_ingredients(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for ingredient name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    List or search ingredients.

    - **search**: Optional search term (uses fulltext index)
    - **category**: Optional category filter
    - **skip**: Pagination offset
    - **limit**: Maximum results (max 200)
    """
    if search:
        # Use fulltext search
        results = db.execute_query(
            Q.SEARCH_INGREDIENTS,
            {"search": search, "limit": limit}
        )
    else:
        # Regular list with optional category filter
        results = db.execute_query(
            Q.LIST_INGREDIENTS,
            {"category": category, "skip": skip, "limit": limit}
        )

    return [IngredientBase(**r) for r in results]


@router.get("/{ingredient_id}", response_model=IngredientDetail)
@limiter.limit("30/minute")
def get_ingredient(
    request: Request,
    ingredient_id: str,
    db: Neo4jService = Depends(get_db)
):
    """
    Get detailed information about a specific ingredient.
    """
    result = db.execute_single(Q.GET_INGREDIENT, {"id": ingredient_id})

    if not result:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return IngredientDetail(**result)


@router.get("/{ingredient_id}/compounds", response_model=list[CompoundInIngredient])
@limiter.limit("30/minute")
def get_ingredient_compounds(
    request: Request,
    ingredient_id: str,
    db: Neo4jService = Depends(get_db)
):
    """
    Get all flavor compounds contained in an ingredient.

    Returns compounds sorted by concentration (highest first).
    """
    # First verify ingredient exists
    ingredient = db.execute_single(Q.GET_INGREDIENT, {"id": ingredient_id})
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    results = db.execute_query(
        Q.GET_INGREDIENT_COMPOUNDS,
        {"id": ingredient_id}
    )

    return [CompoundInIngredient(**r) for r in results]


@router.get("/{ingredient_id}/pairings", response_model=list[Pairing])
@limiter.limit("30/minute")
def get_ingredient_pairings(
    request: Request,
    ingredient_id: str,
    min_score: float = Query(0.3, ge=0, le=1, description="Minimum pairing score"),
    limit: int = Query(20, ge=1, le=100, description="Maximum pairings to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    Get pairing recommendations for an ingredient.

    - **min_score**: Minimum pairing score (0-1)
    - **limit**: Maximum results

    Returns pairings sorted by score (best first).
    """
    # First verify ingredient exists
    ingredient = db.execute_single(Q.GET_INGREDIENT, {"id": ingredient_id})
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    results = db.execute_query(
        Q.GET_PAIRINGS,
        {"id": ingredient_id, "min_score": min_score, "limit": limit}
    )

    return [Pairing(**r) for r in results]


@router.get("/{id1}/compare/{id2}", response_model=ComparisonResult)
@limiter.limit("30/minute")
def compare_ingredients(
    request: Request,
    id1: str,
    id2: str,
    db: Neo4jService = Depends(get_db)
):
    """
    Compare two ingredients and show their shared flavor compounds.

    Returns:
    - Shared compounds with concentrations in each ingredient
    - Overall pairing score if available
    """
    # Verify both ingredients exist
    ing1 = db.execute_single(Q.GET_INGREDIENT, {"id": id1})
    if not ing1:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    ing2 = db.execute_single(Q.GET_INGREDIENT, {"id": id2})
    if not ing2:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    # Get shared compounds
    shared_results = db.execute_query(
        Q.COMPARE_INGREDIENTS,
        {"id1": id1, "id2": id2}
    )

    shared_compounds = [SharedCompound(**r) for r in shared_results]

    # Get pairing score if it exists
    pairing = db.execute_single(
        Q.GET_PAIRING_SCORE,
        {"id1": id1, "id2": id2}
    )

    return ComparisonResult(
        ingredient_1=IngredientBase(**ing1),
        ingredient_2=IngredientBase(**ing2),
        shared_compounds=shared_compounds,
        shared_count=len(shared_compounds),
        pairing_score=pairing["score"] if pairing else None,
        explanation=pairing["explanation"] if pairing else None,
    )
