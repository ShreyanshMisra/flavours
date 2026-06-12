"""
Pytest configuration.

The api/ package uses imports relative to its own directory
(e.g. `from routes import ingredients`), so api/ must be on sys.path
before the tests import the app. A dummy Neo4j password is provided so
the app can be imported without a .env file (e.g. in CI); the tests
never talk to a real database.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

os.environ.setdefault("NEO4J_PASSWORD", "test-only-password")
