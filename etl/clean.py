"""
Data Cleaning and Normalization Script

Processes raw FlavorDB data into cleaned, normalized format.
Output: data/processed/ingredients.json, compounds.json, categories.json
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
COMPOUNDS_DIR = RAW_DATA_DIR / "compounds"


def ensure_directories():
    """Create output directories if they don't exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


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


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def normalize_name(name: str) -> str:
    """Normalize ingredient/compound name for display."""
    if not name:
        return ""
    # Capitalize first letter of each word, handle special cases
    name = name.strip()
    # Title case but preserve some abbreviations
    words = name.split()
    normalized = []
    for word in words:
        if word.upper() in ['DNA', 'RNA', 'ATP', 'ADP']:
            normalized.append(word.upper())
        else:
            normalized.append(word.capitalize())
    return ' '.join(normalized)


def extract_category(entity: dict) -> tuple[str, str]:
    """
    Extract category and subcategory from entity data.

    Returns:
        Tuple of (category, subcategory)
    """
    # FlavorDB uses 'category' field
    category_raw = entity.get('category', '').lower().strip()

    # Map FlavorDB categories to our categories
    category_mapping = {
        'fruit': ('fruit', ''),
        'vegetable': ('vegetable', ''),
        'spice': ('spice', ''),
        'herb': ('herb', ''),
        'meat': ('protein', 'meat'),
        'fish': ('protein', 'fish'),
        'seafood': ('protein', 'seafood'),
        'poultry': ('protein', 'poultry'),
        'dairy': ('dairy', ''),
        'cereal': ('grain', 'cereal'),
        'grain': ('grain', ''),
        'legume': ('legume', ''),
        'nut': ('nut', ''),
        'seed': ('seed', ''),
        'beverage': ('beverage', ''),
        'alcoholic beverage': ('beverage', 'alcoholic'),
        'plant': ('plant', ''),
        'fungus': ('fungus', ''),
        'animal product': ('animal product', ''),
        'flower': ('plant', 'flower'),
        'additive': ('additive', ''),
        'bakery': ('bakery', ''),
        'dish': ('dish', ''),
        'plant derivative': ('plant', 'derivative'),
        'essential oil': ('oil', 'essential'),
    }

    if category_raw in category_mapping:
        return category_mapping[category_raw]

    # Default: use raw category
    return (category_raw if category_raw else 'other', '')


def calculate_concentration(molecule_data: dict, max_concentration: float) -> float:
    """
    Calculate normalized concentration (0-1) for a molecule.

    Uses fooddb_flavor_profile or other available metrics.
    """
    # Try to get concentration from various fields
    # FlavorDB may have different fields depending on the version

    # Default to a mid-range value if no concentration data
    concentration = 0.5

    # Check for flavor profile score
    if 'fooddb_flavor_profile' in molecule_data:
        profile = molecule_data['fooddb_flavor_profile']
        if profile and isinstance(profile, (int, float)):
            concentration = min(float(profile) / 100, 1.0)

    # Normalize against max if provided
    if max_concentration > 0:
        concentration = concentration / max_concentration

    return round(min(max(concentration, 0.0), 1.0), 4)


def extract_taste_profiles(odor_description: str) -> list[str]:
    """
    Extract taste profiles from odor description.

    Returns list of taste profiles: sweet, sour, bitter, salty, umami
    """
    if not odor_description:
        return []

    odor_lower = odor_description.lower()
    profiles = []

    taste_keywords = {
        'sweet': ['sweet', 'sugar', 'honey', 'caramel', 'vanilla', 'fruity'],
        'sour': ['sour', 'acidic', 'tart', 'citrus', 'vinegar', 'fermented'],
        'bitter': ['bitter', 'astringent', 'harsh', 'coffee', 'dark'],
        'salty': ['salty', 'briny', 'saline', 'marine'],
        'umami': ['umami', 'savory', 'meaty', 'brothy', 'fermented', 'cheese', 'mushroom'],
    }

    for taste, keywords in taste_keywords.items():
        if any(kw in odor_lower for kw in keywords):
            profiles.append(taste)

    return profiles


def process_entities() -> tuple[list, dict]:
    """
    Process raw entity data into cleaned ingredients.

    Returns:
        Tuple of (ingredients_list, category_counts)
    """
    entities_file = RAW_DATA_DIR / "entities.json"
    entities = load_json(entities_file)

    if not entities:
        logger.error("No entities found. Run fetch.py first.")
        return [], {}

    ingredients = []
    category_counts = defaultdict(int)
    seen_ids = set()

    for entity in entities:
        entity_id = entity.get('entity_id')
        if not entity_id or entity_id in seen_ids:
            continue
        seen_ids.add(entity_id)

        # Get readable name
        name_raw = entity.get('entity_alias_readable') or entity.get('entity_alias', '')
        name = normalize_name(name_raw)

        if not name:
            continue

        # Generate slug ID
        slug_id = slugify(name)
        if not slug_id:
            slug_id = f"entity-{entity_id}"

        # Extract category
        category, subcategory = extract_category(entity)
        category_counts[category] += 1

        # Build aliases list
        aliases = []
        if entity.get('entity_alias') and entity.get('entity_alias') != name_raw:
            aliases.append(entity.get('entity_alias'))

        # Check if we have detailed compound data for this entity
        compound_file = COMPOUNDS_DIR / f"{entity_id}.json"
        has_compounds = compound_file.exists()

        ingredient = {
            'id': slug_id,
            'entity_id': entity_id,  # Keep original ID for compound lookup
            'name': name,
            'aliases': aliases,
            'category': category,
            'subcategory': subcategory,
            'has_compounds': has_compounds,
        }

        ingredients.append(ingredient)

    logger.info(f"Processed {len(ingredients)} ingredients")
    return ingredients, dict(category_counts)


def process_molecules() -> list:
    """
    Process raw molecule data into cleaned compounds.

    Extracts molecules from individual entity detail files since FlavorDB
    no longer provides a separate molecules list endpoint.

    Returns:
        List of cleaned compound dictionaries
    """
    compounds = []
    seen_ids = set()

    # First check if molecules.json exists (old format)
    molecules_file = RAW_DATA_DIR / "molecules.json"
    if molecules_file.exists():
        molecules = load_json(molecules_file)
        if molecules:
            logger.info(f"Found molecules.json with {len(molecules)} molecules")
            for mol in molecules:
                pubchem_id = mol.get('pubchem_id')
                if pubchem_id and pubchem_id not in seen_ids:
                    seen_ids.add(pubchem_id)
                    compounds.append(_process_single_molecule(mol))
            return compounds

    # Extract molecules from entity detail files
    logger.info("Extracting molecules from entity detail files...")

    if not COMPOUNDS_DIR.exists():
        logger.error("No compound files found. Run fetch.py first.")
        return []

    entity_files = list(COMPOUNDS_DIR.glob("*.json"))
    if not entity_files:
        logger.error("No entity detail files found. Run fetch.py first.")
        return []

    for entity_file in entity_files:
        entity_data = load_json(entity_file)
        if not entity_data:
            continue

        molecules = entity_data.get('molecules', [])
        for mol in molecules:
            pubchem_id = mol.get('pubchem_id')
            if not pubchem_id or pubchem_id in seen_ids:
                continue
            seen_ids.add(pubchem_id)
            compounds.append(_process_single_molecule(mol))

    logger.info(f"Processed {len(compounds)} unique compounds from {len(entity_files)} entity files")
    return compounds


def _process_single_molecule(mol: dict) -> dict:
    """Process a single molecule into compound format."""
    pubchem_id = mol.get('pubchem_id')

    # Get name
    common_name = mol.get('common_name', '')
    iupac_name = mol.get('iupac_name', '')

    # Prefer common name, fall back to IUPAC
    name = common_name if common_name else iupac_name
    if not name:
        name = f"Compound {pubchem_id}"

    # Get odor/flavor description
    odor = mol.get('flavor_profile', '') or mol.get('odor', '') or ''

    # Extract taste profiles
    taste_profiles = extract_taste_profiles(odor)

    return {
        'id': str(pubchem_id),
        'pubchem_id': pubchem_id,
        'name': name,
        'common_name': common_name,
        'iupac_name': iupac_name,
        'formula': mol.get('molecular_formula', ''),
        'odor_description': odor,
        'taste_profiles': taste_profiles,
        'cas_number': mol.get('cas_id', ''),
    }


def process_ingredient_compounds(ingredients: list, compounds_lookup: dict) -> list:
    """
    Process compound relationships for each ingredient.

    Returns:
        List of ingredient-compound relationships
    """
    relationships = []

    for ingredient in ingredients:
        entity_id = ingredient.get('entity_id')
        if not entity_id:
            continue

        # Load detailed entity data
        entity_file = COMPOUNDS_DIR / f"{entity_id}.json"
        entity_details = load_json(entity_file)

        if not entity_details:
            continue

        # Extract molecules from entity details
        molecules = entity_details.get('molecules', [])

        if not molecules:
            continue

        # Find max concentration for normalization
        max_conc = 1.0

        for mol in molecules:
            pubchem_id = str(mol.get('pubchem_id', ''))

            if not pubchem_id or pubchem_id not in compounds_lookup:
                continue

            # Calculate concentration
            concentration = calculate_concentration(mol, max_conc)

            relationship = {
                'ingredient_id': ingredient['id'],
                'compound_id': pubchem_id,
                'concentration': concentration,
                'source': 'flavordb',
            }

            relationships.append(relationship)

    logger.info(f"Processed {len(relationships)} ingredient-compound relationships")
    return relationships


def build_categories(category_counts: dict) -> list:
    """Build category nodes from counts."""
    categories = []

    # Define category hierarchy
    category_parents = {
        'meat': 'protein',
        'fish': 'protein',
        'seafood': 'protein',
        'poultry': 'protein',
        'cereal': 'grain',
        'alcoholic': 'beverage',
        'essential': 'oil',
        'derivative': 'plant',
        'flower': 'plant',
    }

    for category, count in category_counts.items():
        cat_entry = {
            'id': slugify(category),
            'name': normalize_name(category),
            'count': count,
            'parent_id': category_parents.get(category),
        }
        categories.append(cat_entry)

    return categories


def build_taste_profiles() -> list:
    """Build standard taste profile nodes."""
    profiles = [
        {
            'id': 'sweet',
            'name': 'Sweet',
            'description': 'Sugary, honey-like, pleasant taste associated with sugars'
        },
        {
            'id': 'sour',
            'name': 'Sour',
            'description': 'Acidic, tart taste associated with citrus and fermentation'
        },
        {
            'id': 'bitter',
            'name': 'Bitter',
            'description': 'Sharp, astringent taste often found in coffee and dark chocolate'
        },
        {
            'id': 'salty',
            'name': 'Salty',
            'description': 'Briny, mineral taste associated with sodium'
        },
        {
            'id': 'umami',
            'name': 'Umami',
            'description': 'Savory, meaty, brothy taste associated with glutamates'
        },
    ]
    return profiles


def clean_all():
    """Run full cleaning pipeline."""
    ensure_directories()

    # Process entities into ingredients
    logger.info("Processing ingredients...")
    ingredients, category_counts = process_entities()

    if not ingredients:
        logger.error("No ingredients processed. Ensure data is fetched first.")
        return

    # Process molecules into compounds
    logger.info("Processing compounds...")
    compounds = process_molecules()

    # Build compounds lookup for relationship processing
    compounds_lookup = {c['id']: c for c in compounds}

    # Process ingredient-compound relationships
    logger.info("Processing ingredient-compound relationships...")
    ingredient_compounds = process_ingredient_compounds(ingredients, compounds_lookup)

    # Build categories
    logger.info("Building categories...")
    categories = build_categories(category_counts)

    # Build taste profiles
    taste_profiles = build_taste_profiles()

    # Filter ingredients to only those with compounds
    ingredient_ids_with_compounds = set(r['ingredient_id'] for r in ingredient_compounds)
    ingredients_with_compounds = [
        ing for ing in ingredients
        if ing['id'] in ingredient_ids_with_compounds
    ]

    logger.info(f"Ingredients with compounds: {len(ingredients_with_compounds)}/{len(ingredients)}")

    # Filter compounds to only those used
    compound_ids_used = set(r['compound_id'] for r in ingredient_compounds)
    compounds_used = [c for c in compounds if c['id'] in compound_ids_used]

    logger.info(f"Compounds used: {len(compounds_used)}/{len(compounds)}")

    # Save processed data
    save_json(ingredients_with_compounds, PROCESSED_DIR / "ingredients.json")
    save_json(compounds_used, PROCESSED_DIR / "compounds.json")
    save_json(ingredient_compounds, PROCESSED_DIR / "ingredient_compounds.json")
    save_json(categories, PROCESSED_DIR / "categories.json")
    save_json(taste_profiles, PROCESSED_DIR / "taste_profiles.json")

    # Save all ingredients (including those without compounds) for reference
    save_json(ingredients, PROCESSED_DIR / "all_ingredients.json")

    logger.info("Cleaning complete!")

    # Print summary
    print("\n=== Cleaning Summary ===")
    print(f"Ingredients (with compounds): {len(ingredients_with_compounds)}")
    print(f"Compounds: {len(compounds_used)}")
    print(f"Ingredient-Compound relations: {len(ingredient_compounds)}")
    print(f"Categories: {len(categories)}")
    print("\nTop categories:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    clean_all()
