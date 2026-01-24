"""
Data Validation Tests

Tests to verify data integrity after ETL processing.
"""

import json
import pytest
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
NEO4J_DIR = DATA_DIR / "neo4j"


def load_json(filepath: Path):
    """Load JSON file if it exists."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


# Skip all tests if processed data doesn't exist
pytestmark = pytest.mark.skipif(
    not (PROCESSED_DIR / "ingredients.json").exists(),
    reason="Processed data not available. Run ETL pipeline first."
)


class TestIngredients:
    """Tests for ingredient data."""

    @pytest.fixture
    def ingredients(self):
        return load_json(PROCESSED_DIR / "ingredients.json")

    def test_ingredients_exist(self, ingredients):
        """Should have at least some ingredients."""
        assert ingredients is not None
        assert len(ingredients) > 0

    def test_ingredients_have_required_fields(self, ingredients):
        """Each ingredient should have required fields."""
        required_fields = ['id', 'name', 'category']

        for ing in ingredients:
            for field in required_fields:
                assert field in ing, f"Ingredient {ing.get('id', 'unknown')} missing {field}"
                assert ing[field], f"Ingredient {ing.get('id', 'unknown')} has empty {field}"

    def test_ingredient_ids_unique(self, ingredients):
        """Ingredient IDs should be unique."""
        ids = [ing['id'] for ing in ingredients]
        assert len(ids) == len(set(ids)), "Duplicate ingredient IDs found"

    def test_ingredient_ids_are_slugs(self, ingredients):
        """Ingredient IDs should be URL-safe slugs."""
        import re
        slug_pattern = re.compile(r'^[a-z0-9-]+$')

        for ing in ingredients:
            assert slug_pattern.match(ing['id']), \
                f"Ingredient ID '{ing['id']}' is not a valid slug"


class TestCompounds:
    """Tests for compound data."""

    @pytest.fixture
    def compounds(self):
        return load_json(PROCESSED_DIR / "compounds.json")

    def test_compounds_exist(self, compounds):
        """Should have at least some compounds."""
        assert compounds is not None
        assert len(compounds) > 0

    def test_compounds_have_required_fields(self, compounds):
        """Each compound should have required fields."""
        required_fields = ['id', 'name']

        for comp in compounds:
            for field in required_fields:
                assert field in comp, f"Compound {comp.get('id', 'unknown')} missing {field}"

    def test_compound_ids_unique(self, compounds):
        """Compound IDs should be unique."""
        ids = [comp['id'] for comp in compounds]
        assert len(ids) == len(set(ids)), "Duplicate compound IDs found"


class TestIngredientCompounds:
    """Tests for ingredient-compound relationships."""

    @pytest.fixture
    def relationships(self):
        return load_json(PROCESSED_DIR / "ingredient_compounds.json")

    @pytest.fixture
    def ingredients(self):
        return load_json(PROCESSED_DIR / "ingredients.json")

    @pytest.fixture
    def compounds(self):
        return load_json(PROCESSED_DIR / "compounds.json")

    def test_relationships_exist(self, relationships):
        """Should have ingredient-compound relationships."""
        assert relationships is not None
        assert len(relationships) > 0

    def test_relationships_have_required_fields(self, relationships):
        """Each relationship should have required fields."""
        required_fields = ['ingredient_id', 'compound_id', 'concentration']

        for rel in relationships:
            for field in required_fields:
                assert field in rel, f"Relationship missing {field}"

    def test_concentrations_normalized(self, relationships):
        """Concentrations should be between 0 and 1."""
        for rel in relationships:
            conc = rel['concentration']
            assert 0 <= conc <= 1, \
                f"Concentration {conc} out of range for {rel['ingredient_id']}"

    def test_relationships_reference_valid_ingredients(self, relationships, ingredients):
        """Relationships should reference existing ingredients."""
        ingredient_ids = {ing['id'] for ing in ingredients}

        for rel in relationships:
            assert rel['ingredient_id'] in ingredient_ids, \
                f"Relationship references unknown ingredient: {rel['ingredient_id']}"

    def test_relationships_reference_valid_compounds(self, relationships, compounds):
        """Relationships should reference existing compounds."""
        compound_ids = {comp['id'] for comp in compounds}

        for rel in relationships:
            assert rel['compound_id'] in compound_ids, \
                f"Relationship references unknown compound: {rel['compound_id']}"


class TestPairings:
    """Tests for pairing data."""

    @pytest.fixture
    def pairings(self):
        return load_json(PROCESSED_DIR / "pairings.json")

    @pytest.fixture
    def ingredients(self):
        return load_json(PROCESSED_DIR / "ingredients.json")

    def test_pairings_exist(self, pairings):
        """Should have computed pairings."""
        assert pairings is not None
        assert len(pairings) > 0

    def test_pairings_have_required_fields(self, pairings):
        """Each pairing should have required fields."""
        required_fields = ['ingredient_a', 'ingredient_b', 'score', 'shared_compounds']

        for pair in pairings:
            for field in required_fields:
                assert field in pair, f"Pairing missing {field}"

    def test_pairing_scores_valid(self, pairings):
        """Pairing scores should be between 0 and 1."""
        for pair in pairings:
            score = pair['score']
            assert 0 <= score <= 1, \
                f"Score {score} out of range for {pair['ingredient_a']} + {pair['ingredient_b']}"

    def test_pairings_reference_valid_ingredients(self, pairings, ingredients):
        """Pairings should reference existing ingredients."""
        ingredient_ids = {ing['id'] for ing in ingredients}

        for pair in pairings:
            assert pair['ingredient_a'] in ingredient_ids, \
                f"Pairing references unknown ingredient: {pair['ingredient_a']}"
            assert pair['ingredient_b'] in ingredient_ids, \
                f"Pairing references unknown ingredient: {pair['ingredient_b']}"

    def test_pairings_have_shared_compounds(self, pairings):
        """Pairings should have at least one shared compound."""
        for pair in pairings:
            assert pair['shared_compounds'] > 0, \
                f"Pairing {pair['ingredient_a']} + {pair['ingredient_b']} has no shared compounds"


class TestNeo4jCSVs:
    """Tests for Neo4j import CSV files."""

    def test_ingredients_csv_exists(self):
        """ingredients.csv should exist."""
        assert (NEO4J_DIR / "ingredients.csv").exists()

    def test_compounds_csv_exists(self):
        """compounds.csv should exist."""
        assert (NEO4J_DIR / "compounds.csv").exists()

    def test_contains_csv_exists(self):
        """contains.csv should exist."""
        assert (NEO4J_DIR / "contains.csv").exists()

    def test_pairs_with_csv_exists(self):
        """pairs_with.csv should exist."""
        assert (NEO4J_DIR / "pairs_with.csv").exists()


class TestKnownPairings:
    """Tests for well-known flavor pairings."""

    @pytest.fixture
    def pairings(self):
        return load_json(PROCESSED_DIR / "pairings.json")

    @pytest.fixture
    def ingredients(self):
        return load_json(PROCESSED_DIR / "ingredients.json")

    def get_pairing_score(self, pairings, ing_a, ing_b):
        """Get pairing score for two ingredients by name substring."""
        ing_a_lower = ing_a.lower()
        ing_b_lower = ing_b.lower()

        for pair in pairings:
            a = pair['ingredient_a'].lower()
            b = pair['ingredient_b'].lower()

            if (ing_a_lower in a and ing_b_lower in b) or \
               (ing_a_lower in b and ing_b_lower in a):
                return pair['score']

        return None

    @pytest.mark.skip(reason="Depends on specific ingredients in dataset")
    def test_tomato_basil_pair_well(self, pairings):
        """Tomato and basil should have a good pairing score."""
        score = self.get_pairing_score(pairings, "tomato", "basil")
        if score is not None:
            assert score > 0.4, f"Tomato + basil score too low: {score}"

    @pytest.mark.skip(reason="Depends on specific ingredients in dataset")
    def test_chocolate_raspberry_pair_well(self, pairings):
        """Chocolate and raspberry should pair well."""
        score = self.get_pairing_score(pairings, "chocolate", "raspberry")
        if score is not None:
            assert score > 0.4, f"Chocolate + raspberry score too low: {score}"
