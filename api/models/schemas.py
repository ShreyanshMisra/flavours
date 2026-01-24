"""
Pydantic Models for API Request/Response Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


# Base models
class IngredientBase(BaseModel):
    """Base ingredient information."""
    id: str
    name: str
    category: str
    subcategory: Optional[str] = ""


class IngredientDetail(IngredientBase):
    """Detailed ingredient information including aliases."""
    aliases: list[str] = []


class CompoundBase(BaseModel):
    """Base compound information."""
    id: str
    name: str
    common_name: Optional[str] = ""


class CompoundDetail(CompoundBase):
    """Detailed compound information."""
    formula: Optional[str] = ""
    odor_description: Optional[str] = ""
    taste_profiles: list[str] = []


class CompoundInIngredient(CompoundBase):
    """Compound with concentration in an ingredient."""
    odor_description: Optional[str] = ""
    concentration: float


class IngredientInCompound(IngredientBase):
    """Ingredient containing a compound with concentration."""
    concentration: float


# Pairing models
class Pairing(BaseModel):
    """Pairing recommendation."""
    id: str
    name: str
    category: str
    score: float = Field(..., ge=0, le=1)
    shared_compounds: int
    key_compounds: list[str] = []
    explanation: str


class SharedCompound(BaseModel):
    """Shared compound between two ingredients."""
    id: str
    name: str
    common_name: Optional[str] = ""
    odor_description: Optional[str] = ""
    concentration_1: float
    concentration_2: float


class ComparisonResult(BaseModel):
    """Result of comparing two ingredients."""
    ingredient_1: IngredientBase
    ingredient_2: IngredientBase
    shared_compounds: list[SharedCompound]
    pairing_score: Optional[float] = None
    shared_count: int
    explanation: Optional[str] = None


# Category and taste profile models
class Category(BaseModel):
    """Ingredient category."""
    id: str
    name: str
    count: int = 0


class TasteProfile(BaseModel):
    """Taste profile."""
    id: str
    name: str
    description: Optional[str] = ""
    compound_count: int = 0


# Graph exploration models
class GraphNode(BaseModel):
    """Node in the graph visualization."""
    id: str
    name: str
    category: Optional[str] = None
    type: str = "ingredient"  # ingredient, compound, category


class GraphLink(BaseModel):
    """Link between nodes in graph visualization."""
    source: str
    target: str
    score: Optional[float] = None
    type: str = "pairs_with"  # pairs_with, contains, belongs_to


class GraphData(BaseModel):
    """Graph data for visualization."""
    nodes: list[GraphNode]
    links: list[GraphLink]


class SurprisePairing(BaseModel):
    """Unexpected pairing between different categories."""
    ingredient_1: IngredientBase
    ingredient_2: IngredientBase
    score: float
    key_compounds: list[str] = []
    explanation: str


# Stats models
class DatabaseStats(BaseModel):
    """Database statistics."""
    ingredients: int
    compounds: int
    contains_relationships: int
    pairings: int


# Response models
class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: list
    total: int
    skip: int
    limit: int


class IngredientListResponse(BaseModel):
    """Response for ingredient list endpoint."""
    items: list[IngredientBase]
    total: int
    skip: int
    limit: int


class CompoundListResponse(BaseModel):
    """Response for compound list endpoint."""
    items: list[CompoundBase]
    total: int
    skip: int
    limit: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    message: Optional[str] = None
