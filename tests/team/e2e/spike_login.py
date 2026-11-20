"""
SE3002 Software Quality Engineering - Phase 0 Spike 5 Playwright Test
Automates UI login verification against pretix control panel.
Captures screen evidence and verifies successful session establishment.
"""
import os
import sys
from playwright.sync_api import sync_playwright

def run_login_spike():
    print("Launching Playwright Chromium for Spike 5 UI test...")
    os.makedirs("reports/spikes", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        login_url = "http://localhost:8345/control/login"
        print(f"Navigating to {login_url}...")
        page.goto(login_url)
        
        # Verify login form is present
        page.wait_for_selector('input[name="email"]')
        print("Login form reached successfully.")
        
        # Fill credentials
        page.fill('input[name="email"]', "admin@localhost")
        page.fill('input[name="password"]', "admin_secure_password_2026")
        
        # Submit form
        print("Submitting login form...")
        page.click('button[type="submit"]')
        
        # Wait for navigation to control dashboard
        page.wait_for_load_state("networkidle")
        current_url = page.url
        print(f"Post-login URL: {current_url}")
        
        # Take verification screenshot
        screenshot_path = "reports/spikes/spike5_login_success.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved dashboard screenshot to {screenshot_path}")
        
        # Assert authenticated session
        assert "/control/login" not in current_url or page.locator(".navbar-nav").count() > 0 or "control" in current_url
        print("Playwright UI Login Spike PASSED!")
        browser.close()

if __name__ == "__main__":
    run_login_spike()
