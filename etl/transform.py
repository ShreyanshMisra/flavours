"""
Data Transformation Script

Computes pairing scores and generates Neo4j-ready CSV files.
Output: data/neo4j/*.csv files for graph import
"""

import csv
import json
import math
import logging
from pathlib import Path
from typing import Optional
from collections import defaultdict
from itertools import combinations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
NEO4J_DIR = Path(__file__).parent.parent / "data" / "neo4j"


def ensure_directories():
    """Create output directories if they don't exist."""
    NEO4J_DIR.mkdir(parents=True, exist_ok=True)


def load_json(filepath: Path) -> Optional[any]:
    """Load data from JSON file if it exists."""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_json(data: any, filepath: Path):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {filepath}")


def save_csv(data: list, filepath: Path, fieldnames: list):
    """Save data to CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Saved: {filepath} ({len(data)} rows)")


def compute_pairing_score(
    compounds_a: dict[str, float],
    compounds_b: dict[str, float],
    compound_names: dict[str, str]
) -> tuple[float, int, list[str], str]:
    """
    Compute pairing score between two ingredients based on shared compounds.

    Args:
        compounds_a: Dict of compound_id -> concentration for ingredient A
        compounds_b: Dict of compound_id -> concentration for ingredient B
        compound_names: Dict of compound_id -> compound name for display

    Returns:
        Tuple of (score, shared_count, key_compounds, explanation)
    """
    # Find shared compounds
    shared = set(compounds_a.keys()) & set(compounds_b.keys())

    if not shared:
        return 0.0, 0, [], "No shared flavor compounds"

    shared_count = len(shared)

    # Calculate weighted overlap using Jaccard-like similarity
    # Weight by concentration to prioritize prominent compounds
    shared_weight = sum(
        min(compounds_a[c], compounds_b[c])
        for c in shared
    )

    total_weight = sum(compounds_a.values()) + sum(compounds_b.values())

    # Normalize to 0-1
    if total_weight > 0:
        raw_score = (2 * shared_weight) / total_weight
    else:
        raw_score = 0

    # Apply diminishing returns for very high overlap
    # This ensures very similar ingredients don't dominate
    score = 1 - math.exp(-3 * raw_score)

    # Boost score slightly based on number of shared compounds
    # More shared compounds = more robust pairing
    compound_bonus = min(shared_count / 20, 0.2)  # Max 0.2 bonus
    score = min(score + compound_bonus, 1.0)

    # Identify key compounds (highest combined concentration)
    key_compound_ids = sorted(
        shared,
        key=lambda c: compounds_a[c] + compounds_b[c],
        reverse=True
    )[:5]

    key_compounds = [compound_names.get(c, c) for c in key_compound_ids]

    # Generate explanation
    explanation = generate_explanation(key_compounds, score, shared_count)

    return round(score, 3), shared_count, key_compounds, explanation


def generate_explanation(key_compounds: list[str], score: float, shared_count: int) -> str:
    """Generate human-readable pairing explanation."""
    if score > 0.8:
        strength = "Excellent"
    elif score > 0.6:
        strength = "Strong"
    elif score > 0.4:
        strength = "Good"
    elif score > 0.2:
        strength = "Subtle"
    else:
        strength = "Weak"

    if len(key_compounds) == 0:
        return f"{strength} pairing"
    elif len(key_compounds) == 1:
        return f"{strength} pairing based on shared {key_compounds[0]}"
    elif len(key_compounds) <= 3:
        compounds_str = ", ".join(key_compounds[:-1]) + f" and {key_compounds[-1]}"
        return f"{strength} pairing; both contain {compounds_str}"
    else:
        return f"{strength} pairing with {shared_count} shared flavor compounds including {key_compounds[0]}"


def build_ingredient_compound_map(ingredient_compounds: list) -> dict[str, dict[str, float]]:
    """
    Build mapping of ingredient_id -> {compound_id: concentration}
    """
    mapping = defaultdict(dict)

    for rel in ingredient_compounds:
        ing_id = rel['ingredient_id']
        comp_id = rel['compound_id']
        conc = rel['concentration']
        mapping[ing_id][comp_id] = conc

    return dict(mapping)


def compute_all_pairings(
    ingredients: list,
    ingredient_compounds: list,
    compounds: list,
    min_score: float = 0.25,
    min_shared: int = 2
) -> list:
    """
    Compute pairings for all ingredient pairs above threshold.

    Args:
        ingredients: List of ingredient dicts
        ingredient_compounds: List of ingredient-compound relationships
        compounds: List of compound dicts
        min_score: Minimum score to include pairing
        min_shared: Minimum shared compounds to include pairing

    Returns:
        List of pairing dicts
    """
    # Build lookup maps
    compound_names = {c['id']: c['name'] for c in compounds}
    ing_compounds = build_ingredient_compound_map(ingredient_compounds)

    # Filter to ingredients with compounds
    ingredient_ids = [ing['id'] for ing in ingredients if ing['id'] in ing_compounds]

    logger.info(f"Computing pairings for {len(ingredient_ids)} ingredients...")

    pairings = []
    total_pairs = len(ingredient_ids) * (len(ingredient_ids) - 1) // 2
    processed = 0
    last_log = 0

    for id_a, id_b in combinations(ingredient_ids, 2):
        processed += 1

        # Progress logging
        if processed - last_log >= 10000:
            logger.info(f"Progress: {processed}/{total_pairs} pairs ({processed * 100 // total_pairs}%)")
            last_log = processed

        # Skip if either ingredient has no compounds
        if id_a not in ing_compounds or id_b not in ing_compounds:
            continue

        score, shared_count, key_compounds, explanation = compute_pairing_score(
            ing_compounds[id_a],
            ing_compounds[id_b],
            compound_names
        )

        # Filter by thresholds
        if score >= min_score and shared_count >= min_shared:
            pairings.append({
                'ingredient_a': id_a,
                'ingredient_b': id_b,
                'score': score,
                'shared_compounds': shared_count,
                'key_compounds': key_compounds,
                'explanation': explanation,
            })

    logger.info(f"Computed {len(pairings)} pairings above threshold")
    return pairings


def generate_neo4j_csvs(
    ingredients: list,
    compounds: list,
    categories: list,
    taste_profiles: list,
    ingredient_compounds: list,
    pairings: list
):
    """Generate CSV files for Neo4j LOAD CSV import."""

    ensure_directories()

    # 1. Ingredients CSV
    ing_fields = ['id', 'name', 'category', 'subcategory', 'aliases']
    ing_rows = []
    for ing in ingredients:
        ing_rows.append({
            'id': ing['id'],
            'name': ing['name'],
            'category': ing['category'],
            'subcategory': ing.get('subcategory', ''),
            'aliases': ';'.join(ing.get('aliases', [])),  # Semi-colon separated
        })
    save_csv(ing_rows, NEO4J_DIR / "ingredients.csv", ing_fields)

    # 2. Compounds CSV
    comp_fields = ['id', 'name', 'common_name', 'formula', 'odor_description', 'taste_profiles']
    comp_rows = []
    for comp in compounds:
        comp_rows.append({
            'id': comp['id'],
            'name': comp['name'],
            'common_name': comp.get('common_name', ''),
            'formula': comp.get('formula', ''),
            'odor_description': comp.get('odor_description', ''),
            'taste_profiles': ';'.join(comp.get('taste_profiles', [])),
        })
    save_csv(comp_rows, NEO4J_DIR / "compounds.csv", comp_fields)

    # 3. Categories CSV
    cat_fields = ['id', 'name', 'parent_id']
    cat_rows = []
    for cat in categories:
        cat_rows.append({
            'id': cat['id'],
            'name': cat['name'],
            'parent_id': cat.get('parent_id', ''),
        })
    save_csv(cat_rows, NEO4J_DIR / "categories.csv", cat_fields)

    # 4. Taste Profiles CSV
    taste_fields = ['id', 'name', 'description']
    taste_rows = []
    for tp in taste_profiles:
        taste_rows.append({
            'id': tp['id'],
            'name': tp['name'],
            'description': tp.get('description', ''),
        })
    save_csv(taste_rows, NEO4J_DIR / "taste_profiles.csv", taste_fields)

    # 5. CONTAINS relationships (ingredient -> compound)
    contains_fields = ['ingredient_id', 'compound_id', 'concentration', 'source']
    contains_rows = []
    for rel in ingredient_compounds:
        contains_rows.append({
            'ingredient_id': rel['ingredient_id'],
            'compound_id': rel['compound_id'],
            'concentration': rel['concentration'],
            'source': rel.get('source', 'flavordb'),
        })
    save_csv(contains_rows, NEO4J_DIR / "contains.csv", contains_fields)

    # 6. BELONGS_TO relationships (ingredient -> category)
    belongs_fields = ['ingredient_id', 'category_id']
    belongs_rows = []
    seen = set()
    for ing in ingredients:
        cat_id = ing['category'].lower().replace(' ', '-')
        key = (ing['id'], cat_id)
        if key not in seen:
            belongs_rows.append({
                'ingredient_id': ing['id'],
                'category_id': cat_id,
            })
            seen.add(key)
    save_csv(belongs_rows, NEO4J_DIR / "belongs_to.csv", belongs_fields)

    # 7. HAS_PROFILE relationships (compound -> taste profile)
    profile_fields = ['compound_id', 'taste_profile_id', 'intensity']
    profile_rows = []
    for comp in compounds:
        for tp in comp.get('taste_profiles', []):
            profile_rows.append({
                'compound_id': comp['id'],
                'taste_profile_id': tp,
                'intensity': 0.7,  # Default intensity
            })
    save_csv(profile_rows, NEO4J_DIR / "has_profile.csv", profile_fields)

    # 8. PAIRS_WITH relationships (ingredient -> ingredient)
    pairs_fields = ['ingredient_a', 'ingredient_b', 'score', 'shared_compounds', 'key_compounds', 'explanation']
    pairs_rows = []
    for pair in pairings:
        pairs_rows.append({
            'ingredient_a': pair['ingredient_a'],
            'ingredient_b': pair['ingredient_b'],
            'score': pair['score'],
            'shared_compounds': pair['shared_compounds'],
            'key_compounds': ';'.join(pair['key_compounds']),
            'explanation': pair['explanation'],
        })
    save_csv(pairs_rows, NEO4J_DIR / "pairs_with.csv", pairs_fields)

    logger.info("Neo4j CSV generation complete!")


def transform_all(min_score: float = 0.25, min_shared: int = 2):
    """Run full transformation pipeline."""

    # Load processed data
    logger.info("Loading processed data...")

    ingredients = load_json(PROCESSED_DIR / "ingredients.json")
    compounds = load_json(PROCESSED_DIR / "compounds.json")
    categories = load_json(PROCESSED_DIR / "categories.json")
    taste_profiles = load_json(PROCESSED_DIR / "taste_profiles.json")
    ingredient_compounds = load_json(PROCESSED_DIR / "ingredient_compounds.json")

    if not all([ingredients, compounds, ingredient_compounds]):
        logger.error("Missing processed data. Run clean.py first.")
        return

    # Compute pairings
    logger.info("Computing pairing scores...")
    pairings = compute_all_pairings(
        ingredients,
        ingredient_compounds,
        compounds,
        min_score=min_score,
        min_shared=min_shared
    )

    # Save pairings JSON for reference
    save_json(pairings, PROCESSED_DIR / "pairings.json")

    # Generate Neo4j CSVs
    logger.info("Generating Neo4j CSV files...")
    generate_neo4j_csvs(
        ingredients,
        compounds,
        categories,
        taste_profiles,
        ingredient_compounds,
        pairings
    )

    # Print summary
    print("\n=== Transformation Summary ===")
    print(f"Ingredients: {len(ingredients)}")
    print(f"Compounds: {len(compounds)}")
    print(f"Ingredient-Compound relations: {len(ingredient_compounds)}")
    print(f"Pairings (score >= {min_score}, shared >= {min_shared}): {len(pairings)}")

    # Top pairings
    if pairings:
        print("\nTop 10 Pairings:")
        for pair in sorted(pairings, key=lambda x: -x['score'])[:10]:
            print(f"  {pair['ingredient_a']} + {pair['ingredient_b']}: {pair['score']:.2f}")
            print(f"    {pair['explanation']}")

    # Surprising pairings (different categories, high score)
    ing_categories = {ing['id']: ing['category'] for ing in ingredients}
    surprising = [
        p for p in pairings
        if ing_categories.get(p['ingredient_a']) != ing_categories.get(p['ingredient_b'])
        and p['score'] > 0.6
    ]

    if surprising:
        print("\nTop 5 Surprising Pairings (different categories):")
        for pair in sorted(surprising, key=lambda x: -x['score'])[:5]:
            cat_a = ing_categories.get(pair['ingredient_a'], '?')
            cat_b = ing_categories.get(pair['ingredient_b'], '?')
            print(f"  {pair['ingredient_a']} ({cat_a}) + {pair['ingredient_b']} ({cat_b}): {pair['score']:.2f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transform data and compute pairings")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.25,
        help="Minimum pairing score to include (default: 0.25)"
    )
    parser.add_argument(
        "--min-shared",
        type=int,
        default=2,
        help="Minimum shared compounds to include (default: 2)"
    )

    args = parser.parse_args()

    transform_all(min_score=args.min_score, min_shared=args.min_shared)
