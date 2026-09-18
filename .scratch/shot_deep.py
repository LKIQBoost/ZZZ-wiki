"""深滚到底，把意象影画/角色展示/攻略各段都截下来。"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1320, "height": 900})
    page.goto("http://127.0.0.1:8551", wait_until="load", timeout=60000)
    page.wait_for_timeout(16000)
    page.mouse.click(430, 300)
    page.wait_for_timeout(10000)

    for i in range(1, 10):
        page.mouse.move(660, 500)
        page.mouse.wheel(0, 1800)
        page.wait_for_timeout(1000)
        page.screenshot(path=f".scratch/shots/s{i}.png")

    browser.close()
print("ok")
