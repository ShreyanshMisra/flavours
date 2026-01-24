"""
FlavorDB Data Acquisition Script

Fetches ingredient and compound data from FlavorDB API.
Output: data/raw/ingredients.json and data/raw/compounds/{ingredient_id}.json
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FlavorDB API configuration
FLAVORDB_BASE = "https://cosylab.iiitd.edu.in/flavordb"
RATE_LIMIT_DELAY = 0.5  # seconds between requests

# Output directories
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
COMPOUNDS_DIR = RAW_DATA_DIR / "compounds"


def ensure_directories():
    """Create output directories if they don't exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    COMPOUNDS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_with_retry(url: str, max_retries: int = 3, timeout: int = 30) -> Optional[dict]:
    """Fetch URL with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"All retries failed for {url}")
                return None


def fetch_all_entities(max_id: int = 1000) -> list:
    """
    Fetch list of all entities (ingredients) from FlavorDB.

    FlavorDB uses 'entity' to refer to food ingredients.
    Since FlavorDB no longer provides a list endpoint, we iterate through IDs.

    Args:
        max_id: Maximum entity ID to try (FlavorDB has ~936 ingredients)
    """
    logger.info(f"Discovering entities by iterating through IDs 1 to {max_id}...")

    entities = []
    consecutive_failures = 0
    max_consecutive_failures = 20  # Stop if we hit 20 404s in a row

    for entity_id in range(1, max_id + 1):
        url = f"{FLAVORDB_BASE}/entities_json?id={entity_id}"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Create a summary entry for the entity list
                entity_summary = {
                    'entity_id': data.get('entity_id'),
                    'entity_alias': data.get('entity_alias'),
                    'entity_alias_readable': data.get('entity_alias_readable'),
                    'category': data.get('category'),
                    'category_readable': data.get('category_readable'),
                    'molecule_count': len(data.get('molecules', []))
                }
                entities.append(entity_summary)
                consecutive_failures = 0

                if len(entities) % 50 == 0:
                    logger.info(f"Discovered {len(entities)} entities so far (ID: {entity_id})...")
            elif response.status_code == 404:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.info(f"Hit {max_consecutive_failures} consecutive 404s at ID {entity_id}, stopping search")
                    break
            else:
                logger.warning(f"Unexpected status {response.status_code} for ID {entity_id}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching ID {entity_id}: {e}")
            consecutive_failures += 1

        # Rate limiting
        time.sleep(0.3)

    logger.info(f"Discovered {len(entities)} entities total")
    return entities


def fetch_entity_details(entity_id: int) -> Optional[dict]:
    """
    Fetch detailed information for a specific entity including its molecules.

    Args:
        entity_id: The FlavorDB entity ID

    Returns:
        Dictionary with entity details and molecules, or None if failed
    """
    # Use the JSON endpoint which returns full data including molecules
    url = f"{FLAVORDB_BASE}/entities_json?id={entity_id}"
    return fetch_with_retry(url)


def fetch_molecule_details(pubchem_id: int) -> Optional[dict]:
    """
    Fetch details for a specific molecule/compound.

    Args:
        pubchem_id: The PubChem compound ID

    Returns:
        Dictionary with molecule details, or None if failed
    """
    url = f"{FLAVORDB_BASE}/molecule_details?id={pubchem_id}"
    return fetch_with_retry(url)


def fetch_all_molecules() -> list:
    """
    Fetch list of all molecules from FlavorDB.

    Note: FlavorDB no longer provides a dedicated molecules list endpoint.
    Molecules are now extracted from entity details during the fetch process.
    This function returns an empty list - molecules are collected inline.
    """
    logger.info("Note: Molecules are collected from entity details (no separate endpoint)")
    return []


def save_json(data: any, filepath: Path):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.debug(f"Saved: {filepath}")


def load_json(filepath: Path) -> Optional[any]:
    """Load data from JSON file if it exists."""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def fetch_and_save_all(skip_existing: bool = True, limit: Optional[int] = None, max_id: int = 1000):
    """
    Fetch all data from FlavorDB and save to disk.

    Args:
        skip_existing: Skip entities that already have saved compound data
        limit: Optional limit on number of entities to fetch (for testing)
        max_id: Maximum entity ID to try when discovering entities
    """
    ensure_directories()

    # Step 1: Discover and fetch all entities
    entities_file = RAW_DATA_DIR / "entities.json"
    entities = []

    if skip_existing and entities_file.exists():
        logger.info("Loading existing entities list...")
        entities = load_json(entities_file) or []

    # If we have an existing list, just verify/update the data
    if entities:
        logger.info(f"Found {len(entities)} entities in cache")
    else:
        # Discover entities by iterating through IDs
        logger.info("Discovering entities (this may take a while)...")

        consecutive_failures = 0
        max_consecutive_failures = 20

        for entity_id in range(1, max_id + 1):
            entity_file = COMPOUNDS_DIR / f"{entity_id}.json"

            # Check if already fetched
            if skip_existing and entity_file.exists():
                existing = load_json(entity_file)
                if existing:
                    entity_summary = {
                        'entity_id': existing.get('entity_id'),
                        'entity_alias': existing.get('entity_alias'),
                        'entity_alias_readable': existing.get('entity_alias_readable'),
                        'category': existing.get('category'),
                        'category_readable': existing.get('category_readable'),
                        'molecule_count': len(existing.get('molecules', []))
                    }
                    entities.append(entity_summary)
                    consecutive_failures = 0
                    continue

            # Fetch entity details
            details = fetch_entity_details(entity_id)

            if details:
                save_json(details, entity_file)
                entity_summary = {
                    'entity_id': details.get('entity_id'),
                    'entity_alias': details.get('entity_alias'),
                    'entity_alias_readable': details.get('entity_alias_readable'),
                    'category': details.get('category'),
                    'category_readable': details.get('category_readable'),
                    'molecule_count': len(details.get('molecules', []))
                }
                entities.append(entity_summary)
                consecutive_failures = 0

                if len(entities) % 50 == 0:
                    logger.info(f"Progress: {len(entities)} entities discovered (ID: {entity_id})")
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.info(f"Hit {max_consecutive_failures} consecutive failures, stopping discovery")
                    break

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

            # Apply limit if specified
            if limit and len(entities) >= limit:
                logger.info(f"Reached limit of {limit} entities")
                break

        # Save entity summary list
        if entities:
            save_json(entities, entities_file)

    if not entities:
        logger.error("No entities found")
        return

    logger.info(f"Completed! Total entities: {len(entities)}")


def fetch_sample_data(sample_size: int = 50):
    """
    Fetch a sample of data for development/testing.

    Fetches entities by iterating through IDs until we have sample_size entities.
    """
    ensure_directories()

    entities = []
    entity_id = 0
    consecutive_failures = 0
    max_consecutive_failures = 20

    logger.info(f"Fetching sample of {sample_size} entities...")

    while len(entities) < sample_size:
        entity_id += 1

        if consecutive_failures >= max_consecutive_failures:
            logger.warning(f"Hit {max_consecutive_failures} consecutive failures, stopping")
            break

        entity_file = COMPOUNDS_DIR / f"{entity_id}.json"

        # Check if already fetched
        if entity_file.exists():
            existing = load_json(entity_file)
            if existing:
                entity_summary = {
                    'entity_id': existing.get('entity_id'),
                    'entity_alias': existing.get('entity_alias'),
                    'entity_alias_readable': existing.get('entity_alias_readable'),
                    'category': existing.get('category'),
                    'category_readable': existing.get('category_readable'),
                    'molecule_count': len(existing.get('molecules', []))
                }
                entities.append(entity_summary)
                logger.info(f"[{len(entities)}/{sample_size}] Loaded (cached): {existing.get('entity_alias_readable', 'Unknown')}")
                consecutive_failures = 0
                continue

        # Fetch entity details
        details = fetch_entity_details(entity_id)

        if details:
            save_json(details, entity_file)
            entity_summary = {
                'entity_id': details.get('entity_id'),
                'entity_alias': details.get('entity_alias'),
                'entity_alias_readable': details.get('entity_alias_readable'),
                'category': details.get('category'),
                'category_readable': details.get('category_readable'),
                'molecule_count': len(details.get('molecules', []))
            }
            entities.append(entity_summary)
            logger.info(f"[{len(entities)}/{sample_size}] Fetched: {details.get('entity_alias_readable', 'Unknown')}")
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            logger.debug(f"ID {entity_id} not found (consecutive failures: {consecutive_failures})")

        time.sleep(RATE_LIMIT_DELAY)

    # Save entity summary list
    if entities:
        save_json(entities, RAW_DATA_DIR / "entities.json")
        logger.info(f"Saved {len(entities)} entity summaries to entities.json")

    logger.info(f"Sample data fetch complete! Fetched {len(entities)} entities.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch data from FlavorDB")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Fetch only a sample of N entities (for testing)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Fetch all entities (may take a while)"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Re-fetch entities even if they already exist"
    )

    args = parser.parse_args()

    if args.sample:
        fetch_sample_data(sample_size=args.sample)
    elif args.full:
        fetch_and_save_all(skip_existing=not args.no_skip)
    else:
        # Default: fetch sample of 50 for quick testing
        logger.info("No arguments provided. Fetching sample of 50 entities.")
        logger.info("Use --full for complete data or --sample N for custom sample size.")
        fetch_sample_data(sample_size=50)
