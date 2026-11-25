"""
Pytest configuration for Defensive Security & Vulnerability Test Suite.
Provides API tokens, authentication headers for Admin, Auditor, and Anonymous clients,
and endpoint mappings for security verification.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path so 'scripts' and other packages are importable
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import requests
from scripts.get_tokens import get_tokens
from scripts.test_secrets import get_test_secret

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
def anonymous_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def invalid_token_headers():
    return {
        "Authorization": "Token malicious_invalid_token_xyz_99999",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="session")
def event_endpoints():
    return {
        "base": BASE_URL,
        "organizer": f"{BASE_URL}/organizers/{ORGANIZER}/",
        "event": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/",
        "items": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/items/",
        "quotas": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/quotas/",
        "quota_avail": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/quotas/1/availability/",
        "orders": f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/orders/",
    }

@pytest.fixture(scope="session")
def admin_password():
    return get_test_secret("SQE_ADMIN_PASSWORD")


@pytest.fixture(scope="session")
def auditor_password():
    return get_test_secret("SQE_AUDITOR_PASSWORD")
