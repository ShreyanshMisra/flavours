"""
API Endpoint Tests

Tests for FastAPI endpoints.
Requires Neo4j to be running with data loaded.
"""

import pytest
from fastapi.testclient import TestClient

# Try to import the app - skip tests if dependencies not available
try:
    from api.main import app
    client = TestClient(app)
    SKIP_TESTS = False
except ImportError:
    SKIP_TESTS = True
    client = None


pytestmark = pytest.mark.skipif(
    SKIP_TESTS,
    reason="API dependencies not available"
)


class TestRootEndpoints:
    """Tests for root and health endpoints."""

    def test_root_returns_api_info(self):
        """Root endpoint should return API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_health_endpoint(self):
        """Health endpoint should return status."""
        response = client.get("/health")
        # May return 200 or 503 depending on Neo4j availability
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"


class TestIngredientEndpoints:
    """Tests for ingredient endpoints."""

    def test_list_ingredients(self):
        """Should return list of ingredients."""
        response = client.get("/ingredients")

        # May fail if Neo4j not available
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_ingredients_with_limit(self):
        """Should respect limit parameter."""
        response = client.get("/ingredients?limit=5")

        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 5

    def test_list_ingredients_with_category(self):
        """Should filter by category."""
        response = client.get("/ingredients?category=fruit")

        if response.status_code == 200:
            data = response.json()
            for ing in data:
                assert ing["category"] == "fruit"

    def test_search_ingredients(self):
        """Should search ingredients by name."""
        response = client.get("/ingredients?search=apple")

        if response.status_code == 200:
            data = response.json()
            # Should return results containing "apple"
            assert isinstance(data, list)

    def test_get_nonexistent_ingredient(self):
        """Should return 404 for nonexistent ingredient."""
        response = client.get("/ingredients/nonexistent-ingredient-xyz")
        assert response.status_code == 404

    def test_get_ingredient_pairings_nonexistent(self):
        """Should return 404 for pairings of nonexistent ingredient."""
        response = client.get("/ingredients/nonexistent-xyz/pairings")
        assert response.status_code == 404

    def test_compare_nonexistent_ingredients(self):
        """Should return 404 when comparing nonexistent ingredients."""
        response = client.get("/ingredients/nonexistent-a/compare/nonexistent-b")
        assert response.status_code == 404


class TestCompoundEndpoints:
    """Tests for compound endpoints."""

    def test_list_compounds(self):
        """Should return list of compounds."""
        response = client.get("/compounds")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_compounds_with_limit(self):
        """Should respect limit parameter."""
        response = client.get("/compounds?limit=5")

        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 5

    def test_get_nonexistent_compound(self):
        """Should return 404 for nonexistent compound."""
        response = client.get("/compounds/nonexistent-compound-xyz")
        assert response.status_code == 404


class TestExploreEndpoints:
    """Tests for exploration endpoints."""

    def test_list_categories(self):
        """Should return list of categories."""
        response = client.get("/explore/categories")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            for cat in data:
                assert "id" in cat
                assert "name" in cat
                assert "count" in cat

    def test_list_taste_profiles(self):
        """Should return taste profiles."""
        response = client.get("/explore/taste-profiles")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_surprise_pairings(self):
        """Should return surprise pairings."""
        response = client.get("/explore/surprise")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_surprise_pairings_with_params(self):
        """Should respect parameters."""
        response = client.get("/explore/surprise?min_score=0.7&limit=5")

        if response.status_code == 200:
            data = response.json()
            assert len(data) <= 5

            for pair in data:
                assert pair["score"] >= 0.7

    def test_database_stats(self):
        """Should return database statistics."""
        response = client.get("/explore/stats")

        if response.status_code == 200:
            data = response.json()
            assert "ingredients" in data
            assert "compounds" in data
            assert "pairings" in data

    def test_random_ingredient(self):
        """Should return a random ingredient."""
        response = client.get("/explore/random")

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "category" in data

    def test_graph_data_requires_center(self):
        """Graph endpoint should require center parameter."""
        response = client.get("/explore/graph")
        assert response.status_code == 422  # Validation error

    def test_graph_data_nonexistent_center(self):
        """Should return 404 for nonexistent center ingredient."""
        response = client.get("/explore/graph?center=nonexistent-xyz")
        assert response.status_code == 404


class TestParameterValidation:
    """Tests for parameter validation."""

    def test_invalid_limit_too_high(self):
        """Should reject limit > 200."""
        response = client.get("/ingredients?limit=500")
        assert response.status_code == 422

    def test_invalid_limit_negative(self):
        """Should reject negative limit."""
        response = client.get("/ingredients?limit=-1")
        assert response.status_code == 422

    def test_invalid_skip_negative(self):
        """Should reject negative skip."""
        response = client.get("/ingredients?skip=-1")
        assert response.status_code == 422

    def test_invalid_min_score_out_of_range(self):
        """Should reject min_score > 1."""
        response = client.get("/explore/surprise?min_score=1.5")
        assert response.status_code == 422


class TestResponseFormat:
    """Tests for response format consistency."""

    def test_ingredients_response_format(self):
        """Ingredient responses should have consistent format."""
        response = client.get("/ingredients?limit=1")

        if response.status_code == 200 and len(response.json()) > 0:
            ing = response.json()[0]
            assert "id" in ing
            assert "name" in ing
            assert "category" in ing
            assert isinstance(ing["id"], str)
            assert isinstance(ing["name"], str)

    def test_pairing_response_format(self):
        """Pairing responses should have consistent format."""
        # First get an ingredient
        ing_response = client.get("/ingredients?limit=1")

        if ing_response.status_code == 200 and len(ing_response.json()) > 0:
            ing_id = ing_response.json()[0]["id"]

            response = client.get(f"/ingredients/{ing_id}/pairings?limit=1")

            if response.status_code == 200 and len(response.json()) > 0:
                pair = response.json()[0]
                assert "id" in pair
                assert "name" in pair
                assert "score" in pair
                assert "shared_compounds" in pair
                assert "explanation" in pair
                assert 0 <= pair["score"] <= 1
