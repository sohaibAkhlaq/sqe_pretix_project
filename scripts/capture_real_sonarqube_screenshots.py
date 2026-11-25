import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.test_secrets import get_test_secret

def capture_real_sonarqube_screenshots():
    base_dir = Path(__file__).resolve().parent.parent
    out_dir = base_dir / "reports" / "static_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard_png = out_dir / "real_sonarqube_dashboard.png"
    measures_png = out_dir / "real_sonarqube_measures.png"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        # 1. Login to SonarQube
        print("[1/3] Navigating to SonarQube login...")
        page.goto("http://localhost:9000/sessions/new", timeout=30000)
        page.wait_for_timeout(2000)
        
        if page.locator("input[name='login']").count() > 0:
            page.fill("input[name='login']", "admin")
            page.fill("input[name='password']", get_test_secret("SONARQUBE_ADMIN_PASSWORD"))
            page.click("button[type='submit']")
            page.wait_for_timeout(3000)
        
        print(f"Current URL after login: {page.url}")
        
        # 2. Capture Dashboard
        target_url = "http://localhost:9000/dashboard?id=sqe-pretix-team"
        print(f"[2/3] Capturing Real Dashboard: {target_url}")
        page.goto(target_url, timeout=30000)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(dashboard_png), full_page=True)
        print(f" -> Saved: {dashboard_png} ({os.path.getsize(dashboard_png)} bytes)")
        
        # 3. Capture Measures (Complexity & Breakdown)
        measures_url = "http://localhost:9000/component_measures?id=sqe-pretix-team"
        print(f"[3/3] Capturing Measures page: {measures_url}")
        page.goto(measures_url, timeout=30000)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(measures_png), full_page=True)
        print(f" -> Saved: {measures_png} ({os.path.getsize(measures_png)} bytes)")
        
        browser.close()
        print("[SUCCESS] Real SonarQube screenshots successfully captured from live container.")

if __name__ == "__main__":
    capture_real_sonarqube_screenshots()
