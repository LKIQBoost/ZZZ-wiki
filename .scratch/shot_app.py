"""截 Flet app 的图：列表页 + 详情页各段。"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1320, "height": 900})
    page.goto("http://127.0.0.1:8551", wait_until="load", timeout=60000)
    page.wait_for_timeout(16000)
    page.screenshot(path=".scratch/shots/app_list.png")
    print("list ok")

    # 第三张卡（克拉蕾），数据齐全
    page.mouse.click(430, 300)
    page.wait_for_timeout(10000)
    page.screenshot(path=".scratch/shots/d1_hero.png")
    print("hero ok")

    for name, dy in [("d2", 900), ("d3", 900), ("d4", 900), ("d5", 900), ("d6", 900)]:
        page.mouse.move(660, 500)
        page.mouse.wheel(0, dy)
        page.wait_for_timeout(1200)
        page.screenshot(path=f".scratch/shots/{name}.png")
        print(name, "ok")

    browser.close()
