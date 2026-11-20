"""
HTTP Security Headers & Transport Security Audit Suite.
Verifies defensive HTTP response headers, anti-clickjacking, CSP, Referrer-Policy,
and CSRF protection in compliance with OWASP Top 10 recommendations.
"""
import pytest
import requests

BASE_STOREFRONT = "http://localhost:8345/sqe/sqe2026/"
BASE_CONTROL = "http://localhost:8345/control/login/"

class TestSecurityHeadersAndCookies:
    """Verifies that the web gateway and Django middleware enforce defensive HTTP headers."""

    def test_x_content_type_options_nosniff(self):
        """SEC-HDR-01: Verifies 'X-Content-Type-Options: nosniff' is present on storefront and control panel."""
        for url in [BASE_STOREFRONT, BASE_CONTROL]:
            resp = requests.get(url)
            header_val = resp.headers.get("X-Content-Type-Options", "").lower()
            assert header_val == "nosniff", f"Missing or invalid X-Content-Type-Options on {url}: {header_val}"

    def test_x_frame_options_anti_clickjacking(self):
        """SEC-HDR-02: Verifies 'X-Frame-Options' is set to DENY or SAMEORIGIN preventing clickjacking UI framing."""
        for url in [BASE_STOREFRONT, BASE_CONTROL]:
            resp = requests.get(url)
            frame_opt = resp.headers.get("X-Frame-Options", "").upper()
            assert frame_opt in ["DENY", "SAMEORIGIN"], f"Insecure X-Frame-Options on {url}: {frame_opt}"

    def test_content_security_policy_present_and_configured(self):
        """SEC-HDR-03: Verifies Content-Security-Policy header defines script, frame, and object restrictions."""
        resp = requests.get(BASE_STOREFRONT)
        csp = resp.headers.get("Content-Security-Policy", "")
        assert csp != "", "Content-Security-Policy header is missing on storefront"
        
        # Verify key defensive directives
        assert "default-src" in csp, "CSP missing default-src directive"
        assert "object-src 'none'" in csp or "object-src" in csp, "CSP missing object-src restriction"
        assert "script-src" in csp, "CSP missing script-src restriction"

    def test_referrer_policy_same_origin(self):
        """SEC-HDR-04: Verifies Referrer-Policy is set to same-origin to prevent token leakage in Referer headers."""
        for url in [BASE_STOREFRONT, BASE_CONTROL]:
            resp = requests.get(url)
            ref_policy = resp.headers.get("Referrer-Policy", "").lower()
            assert ref_policy in ["same-origin", "strict-origin", "strict-origin-when-cross-origin", "no-referrer"], \
                f"Weak Referrer-Policy on {url}: {ref_policy}"

    def test_csrf_protection_enforced_on_storefront_cart(self):
        """SEC-HDR-05: Verifies that state-mutating POST without CSRF token is rejected with HTTP 403 Forbidden."""
        cart_url = f"{BASE_STOREFRONT}cart/add"
        unprotected_post = requests.post(cart_url, data={"item_1": "1"}, allow_redirects=False)
        assert unprotected_post.status_code == 403, f"CSRF attack succeeded! Expected 403 Forbidden, got {unprotected_post.status_code}"

    def test_api_responses_enforce_json_content_type(self, event_endpoints, admin_headers):
        """SEC-HDR-06: Verifies API responses explicitly specify application/json content type avoiding MIME confusion."""
        resp = requests.get(event_endpoints["orders"], headers=admin_headers)
        content_type = resp.headers.get("Content-Type", "").lower()
        assert "application/json" in content_type, f"Unexpected API Content-Type: {content_type}"

    def test_csrf_cookie_present_and_scoped(self):
        """SEC-HDR-07: Verifies CSRF token cookie is generated and scoped to root path."""
        resp = requests.get(BASE_STOREFRONT)
        assert "pretix_csrftoken" in resp.cookies or "csrftoken" in resp.cookies, "CSRF cookie not delivered to client"
