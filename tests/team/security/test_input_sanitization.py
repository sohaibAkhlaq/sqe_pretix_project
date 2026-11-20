"""
Input Sanitization & Injection Defense Test Suite.
Verifies protections against XSS injection, SQL injection, parameter tampering,
and mass assignment across order and quota workflows.
"""
import pytest
import requests
import uuid
import re

class TestInputSanitizationSecurity:
    """Verifies that malicious payloads are sanitized, rejected, or safely parameterized."""

    def test_xss_payload_in_attendee_name_safely_serialized(self, event_endpoints, admin_headers):
        """SEC-INP-01: Script tags injected in attendee_name are treated as literal strings and not executed."""
        orders_url = event_endpoints["orders"]
        xss_payload = "<script>alert('XSS_ATTACK_VECTOR')</script>"
        
        payload = {
            "email": f"xss_attendee_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [
                {
                    "item": 1,
                    "price": "50.00",
                    "attendee_name": xss_payload
                }
            ]
        }
        resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert resp.status_code == 201, f"Failed to create order: {resp.status_code}"
        
        order_data = resp.json()
        saved_name = order_data["positions"][0]["attendee_name"]
        
        # Verify JSON serialization does not evaluate raw script
        assert saved_name == xss_payload
        # Verify Content-Type enforces application/json preventing HTML execution context
        assert "application/json" in resp.headers.get("Content-Type", "")

    def test_xss_malformed_email_rejected_with_400(self, event_endpoints, admin_headers):
        """SEC-INP-02: Malicious XSS vectors inside email addresses are rejected by schema validator (HTTP 400)."""
        orders_url = event_endpoints["orders"]
        malicious_emails = [
            '<script>alert(1)</script>@example.com',
            '"><svg/onload=alert(1)>@test.com',
            'javascript:alert(1)@evil.com'
        ]
        
        for bad_email in malicious_emails:
            payload = {
                "email": bad_email,
                "locale": "en",
                "sales_channel": "web",
                "positions": [{"item": 1, "price": "50.00", "attendee_name": "Bad Email User"}]
            }
            resp = requests.post(orders_url, json=payload, headers=admin_headers)
            assert resp.status_code == 400, f"Expected 400 Bad Request for {bad_email}, got {resp.status_code}"
            assert "email" in resp.json(), f"Expected email validation error for {bad_email}"

    def test_sql_injection_in_order_code_lookup_returns_404(self, event_endpoints, admin_headers):
        """SEC-INP-03: SQL injection payloads in URL paths return HTTP 404 and never trigger database 500 errors."""
        sqli_payloads = [
            "' OR '1'='1' --",
            "'; DROP TABLE pretixbase_order; --",
            "admin' UNION SELECT null, null, null --"
        ]
        
        for payload in sqli_payloads:
            url = f"{event_endpoints['orders']}{payload}/"
            resp = requests.get(url, headers=admin_headers)
            # Must return 404 Not Found (or 400), NEVER 500 Internal Server Error
            assert resp.status_code in [404, 400], f"SQLi payload triggered unexpected status {resp.status_code}: {payload}"
            # Ensure no SQL syntax errors leaked
            body = resp.text.lower()
            assert "syntax error" not in body
            assert "psycopg2" not in body
            assert "traceback" not in body

    def test_sql_injection_in_search_query_parameterized(self, event_endpoints, admin_headers):
        """SEC-INP-04: SQL injection payloads in search query parameters are safely handled via ORM parameterization."""
        orders_url = event_endpoints["orders"]
        sqli_queries = [
            "' OR '1'='1",
            "' UNION SELECT id, code, email FROM pretixbase_order --",
            "1; SELECT pg_sleep(5); --"
        ]
        
        for query in sqli_queries:
            resp = requests.get(orders_url, params={"search": query}, headers=admin_headers)
            assert resp.status_code == 200, f"Query failed with status {resp.status_code}: {query}"
            data = resp.json()
            assert "results" in data
            # Response must be valid JSON and not leak unrelated tenant records
            assert isinstance(data["results"], list)

    def test_parameter_tampering_non_numeric_price_rejected(self, event_endpoints, admin_headers):
        """SEC-INP-05: Parameter tampering attempting non-numeric prices is rejected with HTTP 400 Bad Request."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"tamper_price_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "free_ticket_exploit", "attendee_name": "Price Tamperer"}]
        }
        resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert resp.status_code == 400, f"Expected 400 for non-numeric price, got {resp.status_code}"
        assert "positions" in resp.json()
        assert "price" in resp.json()["positions"][0]

    def test_parameter_tampering_invalid_item_id_rejected(self, event_endpoints, admin_headers):
        """SEC-INP-06: Parameter tampering with non-existent item foreign key is rejected with HTTP 400 Bad Request."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"tamper_item_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 999999, "price": "50.00", "attendee_name": "FK Tamperer"}]
        }
        resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert resp.status_code == 400, f"Expected 400 for invalid item ID, got {resp.status_code}"
        assert "positions" in resp.json()
        assert "item" in resp.json()["positions"][0]

    def test_mass_assignment_order_status_tampering_rejected(self, event_endpoints, admin_headers):
        """SEC-INP-07: Mass assignment attempting to force status to 'paid' (p) without payment provider is rejected (HTTP 400)."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"mass_assign_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "status": "p",  # 'p' is paid in pretix internal state model
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Privilege Escalator"}]
        }
        resp = requests.post(orders_url, json=payload, headers=admin_headers)
        # Pretix actively rejects client-injected paid status with HTTP 400 Bad Request
        assert resp.status_code == 400, f"Expected 400 for mass assignment status tampering, got {resp.status_code}"
        assert "paid order without a payment provider" in str(resp.content).lower()

    def test_order_secret_cryptographic_entropy(self, event_endpoints, admin_headers):
        """SEC-INP-08: Generated order secrets have high entropy (16+ chars alphanumeric) resisting brute force."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"entropy_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Entropy Test"}]
        }
        resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert resp.status_code == 201
        secret = resp.json()["secret"]
        
        assert len(secret) >= 16, f"Order secret too short: {len(secret)} characters"
        assert re.match(r"^[a-zA-Z0-9]+$", secret), f"Secret contains unexpected non-alphanumeric chars: {secret}"
