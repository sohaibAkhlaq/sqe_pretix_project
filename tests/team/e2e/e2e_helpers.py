"""
Shared E2E Test Helpers for Playwright and Pretix State Verification.
Provides deterministic setup, API read-backs, quota monitoring, and browser navigation.
"""
import os
import uuid
import requests
from scripts.get_tokens import get_tokens
from scripts.reset import find_docker_bin, run_reset_once

BASE_URL = "http://localhost:8345"
SCREENSHOT_DIR = os.path.join("reports", "e2e", "screenshots")

def get_admin_headers():
    tokens = get_tokens()
    admin_token = tokens["SQE Test API Token"]
    return {
        "Authorization": f"Token {admin_token}",
        "Content-Type": "application/json"
    }

def get_quota_availability():
    """Reads current available quota number from the REST API."""
    headers = get_admin_headers()
    url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/"
    r = requests.get(url, headers=headers)
    assert r.status_code == 200, f"Failed to get quota: {r.text}"
    return r.json()["available_number"]

def get_order_by_code(order_code):
    """Reads order details directly from REST API."""
    headers = get_admin_headers()
    url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/"
    r = requests.get(url, headers=headers)
    assert r.status_code == 200, f"Failed to get order {order_code}: {r.text}"
    return r.json()

def ensure_quota_headroom(min_headroom=3):
    """Ensures at least min_headroom tickets are available, resetting if depleted."""
    avail = get_quota_availability()
    if avail < min_headroom:
        run_reset_once(find_docker_bin())
    return get_quota_availability()

def create_order_via_api(positions=1, email=None, status="n"):
    """Creates an order via API for fast test fixtures."""
    ensure_quota_headroom(min_headroom=positions)
    headers = get_admin_headers()
    if email is None:
        email = f"e2e_fixture_{uuid.uuid4().hex[:6]}@example.com"
    
    pos_list = []
    for i in range(positions):
        pos_list.append({
            "item": 1,
            "price": "50.00",
            "attendee_name": f"Attendee {i+1}"
        })
    
    payload = {
        "email": email,
        "locale": "en",
        "sales_channel": "web",
        "positions": pos_list
    }
    url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/"
    r = requests.post(url, json=payload, headers=headers)
    assert r.status_code == 201, f"Failed to create order fixture: {r.text}"
    data = r.json()
    order_code = data["code"]
    
    if status == "p":
        pay_url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_paid/"
        pr = requests.post(pay_url, headers=headers)
        assert pr.status_code in [200, 201]
    elif status == "c":
        can_url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/"
        cr = requests.post(can_url, headers=headers)
        assert cr.status_code in [200, 201]
    elif status == "e":
        exp_url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_expired/"
        er = requests.post(exp_url, headers=headers)
        assert er.status_code in [200, 201]
        
    return get_order_by_code(order_code)

def complete_storefront_checkout(page, count=1, email=None, locale="en", company=None):
    """Executes storefront checkout flow via Playwright and returns (order_code, secret)."""
    ensure_quota_headroom(min_headroom=count)
    if email is None:
        email = f"buyer_{uuid.uuid4().hex[:6]}@example.com"
        
    url = f"{BASE_URL}/sqe/sqe2026/?locale={locale}"
    page.goto(url)
    page.wait_for_load_state("networkidle")
    
    # 1. Select quantity
    item_input = page.locator("#item_1")
    if item_input.count() > 0:
        item_input.fill(str(count))
    page.click("#btn-add-to-cart")
    
    # 2. Proceed to checkout
    checkout_btn = page.locator('a:has-text("Proceed with checkout"), a:has-text("Zur Kasse"), button:has-text("Proceed with checkout")').first
    checkout_btn.wait_for(timeout=15000)
    checkout_btn.click()
    page.wait_for_load_state("networkidle")
    
    # 3. Questions step
    email_field = page.locator('input[name="email"]')
    if email_field.count() > 0:
        email_field.fill(email)
    if company:
        is_biz = page.locator('input[name="is_business"]')
        if is_biz.count() > 0:
            is_biz.last.check(force=True)
            page.wait_for_timeout(500)
        comp_field = page.locator('input[name="company"]')
        if comp_field.count() > 0:
            comp_field.fill(company, force=True)
            
    page.locator("button.btn-block.btn-primary").click()
    page.wait_for_load_state("networkidle")
    
    # 4. Payment step
    if "payment" in page.url:
        radios = page.locator('input[name="payment"]')
        if radios.count() > 0:
            radios.first.check(force=True)
        page.locator("button.btn-block.btn-primary").click()
        page.wait_for_load_state("networkidle")
        
    # 5. Confirm step
    if "confirm" in page.url:
        bind_btn = page.locator('button:has-text("Place binding order"), button:has-text("Kostenpflichtig bestellen")').first
        if bind_btn.count() > 0 and bind_btn.is_visible():
            bind_btn.click()
        else:
            page.locator("button.btn-block.btn-primary").click()
        page.wait_for_url(lambda u: "/order/" in u, timeout=15000)
        page.wait_for_load_state("networkidle")
        
    # Parse code and secret from URL /sqe/sqe2026/order/{code}/{secret}/
    curr_url = page.url
    parts = curr_url.split("/")
    order_code = None
    secret = None
    if "order" in parts:
        idx = parts.index("order")
        if len(parts) > idx + 1:
            order_code = parts[idx + 1]
        if len(parts) > idx + 2:
            secret = parts[idx + 2].split("?")[0]
            
    return order_code, secret
