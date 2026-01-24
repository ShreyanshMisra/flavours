"""
Flavor Pairing Knowledge Graph API

FastAPI application for querying the flavor pairing knowledge graph.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from .routes import ingredients, compounds, explore
from .services.neo4j_service import get_neo4j_service, close_neo4j_service
from .models.schemas import HealthResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://flavours-neo4j.vercel.app,https://flavours-api.onrender.com").split(",")
API_KEY = os.getenv("API_KEY", "")
API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Verify API key if required."""
    if not API_KEY_REQUIRED:
        return api_key

    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API key required in X-API-Key header"},
        )
    return api_key


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (restrict browser features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy (API returns JSON, so strict CSP)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: verify database connection
    service = get_neo4j_service()
    if not service.verify_connectivity():
        logger.warning("Could not connect to Neo4j database")
    else:
        logger.info("Connected to Neo4j database")

    # Log security configuration
    logger.info(f"CORS origins: {CORS_ORIGINS}")
    logger.info(f"API key required: {API_KEY_REQUIRED}")

    yield

    # Shutdown: close database connection
    close_neo4j_service()
    logger.info("Closed Neo4j connection")


# Create FastAPI app
app = FastAPI(
    title="Flavor Pairing API",
    description="""
    API for exploring flavor pairings based on shared chemical compounds.

    ## Features

    - **Search Ingredients**: Find ingredients by name or category
    - **Get Pairings**: Discover ingredients that pair well together
    - **Compare Ingredients**: See shared compounds between two ingredients
    - **Explore Graph**: Get data for visualizing ingredient relationships
    - **Surprise Me**: Find unexpected but scientifically-backed pairings

    ## Authentication

    When API key is required, include the `X-API-Key` header with your API key.

    ## Rate Limiting

    API is rate limited to 30 requests per minute per IP address.

    ## Data Source

    Based on FlavorDB molecular gastronomy data mapping flavor compounds
    to ingredients.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware (before CORS)
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # Set to True only if you need cookies/auth headers
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Include routers
app.include_router(ingredients.router)
app.include_router(compounds.router)
app.include_router(explore.router)


@app.get("/", tags=["root"])
@limiter.limit("30/minute")
def root(request: Request):
    """API root endpoint."""
    return {
        "name": "Flavor Pairing API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "ingredients": "/ingredients",
            "compounds": "/compounds",
            "explore": "/explore",
            "health": "/health",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """
    Health check endpoint.

    Verifies API and database connectivity.
    Note: This endpoint is not rate limited and does not require authentication.
    """
    service = get_neo4j_service()

    if service.verify_connectivity():
        return HealthResponse(
            status="healthy",
            database="connected",
            message="All systems operational"
        )
    else:
        raise HTTPException(
            status_code=503,
            detail=HealthResponse(
                status="unhealthy",
                database="disconnected",
                message="Cannot connect to Neo4j database"
            ).model_dump()
        )


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
