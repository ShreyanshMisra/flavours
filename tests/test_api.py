"""
API Endpoint Tests

Tests for FastAPI endpoints against an in-memory fake of the Neo4j
service, so they run (and can fail meaningfully) without a database.
"""

import pytest
from fastapi.testclient import TestClient

import main
from main import app
from services.neo4j_service import (
    get_db,
    IngredientQueries,
    CompoundQueries,
    ExploreQueries,
)


# --- Fixture data -----------------------------------------------------------

INGREDIENTS = {
    "basil": {"id": "basil", "name": "Basil", "category": "herb",
              "subcategory": "", "aliases": ["sweet basil"]},
    "tomato": {"id": "tomato", "name": "Tomato", "category": "fruit",
               "subcategory": "", "aliases": []},
    "garlic": {"id": "garlic", "name": "Garlic", "category": "herb",
               "subcategory": "", "aliases": []},
}

PAIRINGS = {
    "basil": [
        {"id": "tomato", "name": "Tomato", "category": "fruit", "score": 0.9,
         "shared_compounds": 5, "key_compounds": ["Linalool"],
         "explanation": "Excellent pairing"},
        {"id": "garlic", "name": "Garlic", "category": "herb", "score": 0.7,
         "shared_compounds": 3, "key_compounds": ["Eugenol"],
         "explanation": "Strong pairing"},
    ],
}

COMPOUNDS = {
    "linalool": {"id": "linalool", "name": "Linalool", "common_name": "linalool",
                 "formula": "C10H18O", "odor_description": "floral",
                 "taste_profiles": ["sweet"]},
}

GRAPH_NEIGHBORS = [
    {"id": "tomato", "name": "Tomato", "category": "fruit", "score": 0.9},
    {"id": "garlic", "name": "Garlic", "category": "herb", "score": 0.7},
]

GRAPH_NEIGHBOR_LINKS = [
    {"source": "garlic", "target": "tomato", "score": 0.6},
]

STATS = {"ingredients": 3, "compounds": 1, "contains": 10, "pairings": 2}


# --- Fake Neo4j service -----------------------------------------------------

class FakeNeo4jService:
    """In-memory stand-in for Neo4jService, dispatching on query constants."""

    def __init__(self):
        self.calls = []

    def verify_connectivity(self):
        return True

    def execute_query(self, query, parameters=None):
        p = parameters or {}
        self.calls.append((query, p))

        if query is IngredientQueries.LIST_INGREDIENTS:
            rows = [i for i in INGREDIENTS.values()
                    if p.get("category") in (None, i["category"])]
            return rows[p["skip"]:p["skip"] + p["limit"]]

        if query is IngredientQueries.SEARCH_INGREDIENTS:
            term = p["search"].lower()
            return [dict(i, score=1.0) for i in INGREDIENTS.values()
                    if term in i["name"].lower()]

        if query is IngredientQueries.GET_PAIRINGS:
            return [pr for pr in PAIRINGS.get(p["id"], [])
                    if pr["score"] >= p["min_score"]][:p["limit"]]

        if query is IngredientQueries.COMPARE_INGREDIENTS:
            return [{"id": "linalool", "name": "Linalool", "common_name": "",
                     "odor_description": "floral",
                     "concentration_1": 0.8, "concentration_2": 0.4}]

        if query is CompoundQueries.LIST_COMPOUNDS:
            return list(COMPOUNDS.values())[p["skip"]:p["skip"] + p["limit"]]

        if query is CompoundQueries.GET_COMPOUND_INGREDIENTS:
            return [dict(INGREDIENTS["basil"], concentration=0.8)]

        if query is ExploreQueries.GET_CATEGORIES:
            return [{"id": "herb", "name": "herb", "count": 2},
                    {"id": "fruit", "name": "fruit", "count": 1}]

        if query is ExploreQueries.GET_TASTE_PROFILES:
            return [{"id": "sweet", "name": "sweet", "description": "",
                     "compound_count": 1}]

        if query is ExploreQueries.SURPRISE_PAIRINGS:
            return [{"id1": "basil", "name1": "Basil", "category1": "herb",
                     "id2": "tomato", "name2": "Tomato", "category2": "fruit",
                     "score": 0.9, "key_compounds": ["Linalool"],
                     "explanation": "Excellent pairing"}]

        if query is ExploreQueries.EXPLORE_GRAPH:
            return GRAPH_NEIGHBORS if p["center"] == "basil" else []

        if query is ExploreQueries.EXPLORE_NEIGHBOR_LINKS:
            return GRAPH_NEIGHBOR_LINKS if p["center"] == "basil" else []

        raise AssertionError(f"Unexpected query: {query}")

    def execute_single(self, query, parameters=None):
        p = parameters or {}
        self.calls.append((query, p))

        if query is IngredientQueries.GET_INGREDIENT:
            return INGREDIENTS.get(p["id"])

        if query is IngredientQueries.GET_PAIRING_SCORE:
            return {"score": 0.9, "shared_compounds": 5,
                    "key_compounds": ["Linalool"],
                    "explanation": "Excellent pairing"}

        if query is CompoundQueries.GET_COMPOUND:
            return COMPOUNDS.get(p["id"])

        if query is ExploreQueries.GET_STATS:
            return STATS

        if "rand()" in query:  # /explore/random uses an inline query
            return INGREDIENTS["basil"]

        raise AssertionError(f"Unexpected query: {query}")


@pytest.fixture
def fake_db():
    fake = FakeNeo4jService()
    app.dependency_overrides[get_db] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture
def client(fake_db):
    return TestClient(app)


# --- Root and health --------------------------------------------------------

class TestRootEndpoints:

    def test_root_returns_api_info(self, client):
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Flavor Pairing API"
        assert "endpoints" in data

    def test_health_healthy(self, client, fake_db, monkeypatch):
        monkeypatch.setattr(main, "get_neo4j_service", lambda: fake_db)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "database": "connected",
            "message": "All systems operational",
        }

    def test_health_unhealthy(self, client, fake_db, monkeypatch):
        fake_db.verify_connectivity = lambda: False
        monkeypatch.setattr(main, "get_neo4j_service", lambda: fake_db)

        response = client.get("/health")
        assert response.status_code == 503


# --- Ingredients ------------------------------------------------------------

class TestIngredientEndpoints:

    def test_list_ingredients(self, client):
        response = client.get("/ingredients")
        assert response.status_code == 200

        names = {i["name"] for i in response.json()}
        assert names == {"Basil", "Tomato", "Garlic"}

    def test_list_ingredients_with_limit(self, client):
        response = client.get("/ingredients?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_ingredients_with_category(self, client):
        response = client.get("/ingredients?category=herb")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert all(i["category"] == "herb" for i in data)

    def test_search_ingredients(self, client):
        response = client.get("/ingredients?search=bas")
        assert response.status_code == 200
        assert [i["id"] for i in response.json()] == ["basil"]

    def test_search_escapes_lucene_special_characters(self, client, fake_db):
        response = client.get("/ingredients", params={"search": 'basil (fresh) + "raw"/2'})
        assert response.status_code == 200

        search_calls = [p for q, p in fake_db.calls
                        if q is IngredientQueries.SEARCH_INGREDIENTS]
        assert search_calls, "search query was never executed"
        assert search_calls[0]["search"] == 'basil \\(fresh\\) \\+ \\"raw\\"\\/2'

    def test_get_ingredient(self, client):
        response = client.get("/ingredients/basil")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Basil"
        assert data["aliases"] == ["sweet basil"]

    def test_get_ingredient_not_found(self, client):
        response = client.get("/ingredients/does-not-exist")
        assert response.status_code == 404

    def test_get_pairings(self, client):
        response = client.get("/ingredients/basil/pairings")
        assert response.status_code == 200

        data = response.json()
        assert [p["id"] for p in data] == ["tomato", "garlic"]
        assert data[0]["score"] == 0.9

    def test_get_pairings_respects_min_score(self, client):
        response = client.get("/ingredients/basil/pairings?min_score=0.8")
        assert response.status_code == 200
        assert [p["id"] for p in response.json()] == ["tomato"]

    def test_compare_ingredients(self, client):
        response = client.get("/ingredients/basil/compare/tomato")
        assert response.status_code == 200

        data = response.json()
        assert data["ingredient_1"]["id"] == "basil"
        assert data["ingredient_2"]["id"] == "tomato"
        assert data["shared_count"] == 1
        assert data["pairing_score"] == 0.9

    def test_compare_unknown_ingredient_returns_404(self, client):
        response = client.get("/ingredients/basil/compare/does-not-exist")
        assert response.status_code == 404


# --- Compounds --------------------------------------------------------------

class TestCompoundEndpoints:

    def test_list_compounds(self, client):
        response = client.get("/compounds")
        assert response.status_code == 200
        assert [c["id"] for c in response.json()] == ["linalool"]

    def test_get_compound(self, client):
        response = client.get("/compounds/linalool")
        assert response.status_code == 200
        assert response.json()["formula"] == "C10H18O"

    def test_get_compound_not_found(self, client):
        response = client.get("/compounds/does-not-exist")
        assert response.status_code == 404


# --- Explore ----------------------------------------------------------------

class TestExploreEndpoints:

    def test_categories(self, client):
        response = client.get("/explore/categories")
        assert response.status_code == 200
        assert {c["id"]: c["count"] for c in response.json()} == \
            {"herb": 2, "fruit": 1}

    def test_surprise_pairings(self, client):
        response = client.get("/explore/surprise")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["ingredient_1"]["id"] == "basil"
        assert data[0]["ingredient_2"]["id"] == "tomato"

    def test_graph_includes_center_neighbors_and_cross_links(self, client):
        response = client.get("/explore/graph?center=basil")
        assert response.status_code == 200

        data = response.json()
        assert [n["id"] for n in data["nodes"]] == ["basil", "tomato", "garlic"]

        center_links = [(l["target"], l["score"]) for l in data["links"]
                        if l["source"] == "basil"]
        assert center_links == [("tomato", 0.9), ("garlic", 0.7)]

        cross_links = [l for l in data["links"] if l["source"] != "basil"]
        assert cross_links == [{"source": "garlic", "target": "tomato",
                                "score": 0.6, "type": "pairs_with"}]

    def test_graph_unknown_center_returns_404(self, client):
        response = client.get("/explore/graph?center=does-not-exist")
        assert response.status_code == 404

    def test_stats(self, client):
        response = client.get("/explore/stats")
        assert response.status_code == 200
        assert response.json() == {
            "ingredients": 3,
            "compounds": 1,
            "contains_relationships": 10,
            "pairings": 2,
        }

    def test_random_ingredient(self, client):
        response = client.get("/explore/random")
        assert response.status_code == 200
        assert response.json()["id"] == "basil"
