"""
Compound API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.neo4j_service import (
    Neo4jService,
    get_db,
    CompoundQueries as Q
)
from models.schemas import (
    CompoundBase,
    CompoundDetail,
    IngredientInCompound,
)

router = APIRouter(prefix="/compounds", tags=["compounds"])

# Rate limiter (shared with main app)
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=list[CompoundBase])
@limiter.limit("30/minute")
def list_compounds(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    List flavor compounds.

    - **skip**: Pagination offset
    - **limit**: Maximum results (max 200)
    """
    results = db.execute_query(
        Q.LIST_COMPOUNDS,
        {"skip": skip, "limit": limit}
    )

    return [CompoundBase(**r) for r in results]


@router.get("/{compound_id}", response_model=CompoundDetail)
@limiter.limit("30/minute")
def get_compound(
    request: Request,
    compound_id: str,
    db: Neo4jService = Depends(get_db)
):
    """
    Get detailed information about a specific flavor compound.
    """
    result = db.execute_single(Q.GET_COMPOUND, {"id": compound_id})

    if not result:
        raise HTTPException(status_code=404, detail="Compound not found")

    return CompoundDetail(**result)


@router.get("/{compound_id}/ingredients", response_model=list[IngredientInCompound])
@limiter.limit("30/minute")
def get_compound_ingredients(
    request: Request,
    compound_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum ingredients to return"),
    db: Neo4jService = Depends(get_db)
):
    """
    Get all ingredients that contain a specific compound.

    Returns ingredients sorted by compound concentration (highest first).
    """
    # First verify compound exists
    compound = db.execute_single(Q.GET_COMPOUND, {"id": compound_id})
    if not compound:
        raise HTTPException(status_code=404, detail="Compound not found")

    results = db.execute_query(
        Q.GET_COMPOUND_INGREDIENTS,
        {"id": compound_id, "limit": limit}
    )

    return [IngredientInCompound(**r) for r in results]
