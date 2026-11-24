"""
Pytest configuration for REST API Integration Test Suite.
Retrieves auth tokens, defines API clients, and manages test state.
"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import requests
from scripts.get_tokens import get_tokens

BASE_URL = "http://localhost:8345/api/v1"
ORGANIZER = "sqe"
EVENT = "sqe2026"

@pytest.fixture(scope="session")
def api_tokens():
    """Fetches seeded tokens from pretix container."""
    return get_tokens()

@pytest.fixture(scope="session")
def admin_token(api_tokens):
    return api_tokens["SQE Test API Token"]

@pytest.fixture(scope="session")
def auditor_token(api_tokens):
    return api_tokens["Auditor Read Token"]

@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {
        "Authorization": f"Token {admin_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def auditor_headers(auditor_token):
    return {
        "Authorization": f"Token {auditor_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def event_endpoints():
    return {
        "organizer": f"{BASE_URL}/organizers/{ORGANIZER}/",
        "event": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/",
        "items": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/items/",
        "quotas": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/quotas/1/availability/",
        "orders": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/orders/",
    }

@pytest.fixture(scope="session")
def generated_data():
    """Loads authoritative generated test vectors from tools/datagen output."""
    import json
    gen_file = BASE_DIR / "reports" / "api" / "generated_data.json"
    if not gen_file.exists():
        from tools.datagen.generator import generate_full_dataset
        data = generate_full_dataset()
        gen_file.parent.mkdir(parents=True, exist_ok=True)
        with open(gen_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    with open(gen_file, "r", encoding="utf-8") as f:
        return json.load(f)

