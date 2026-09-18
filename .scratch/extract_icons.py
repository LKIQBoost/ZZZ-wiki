"""一次性抽取属性图标。

属性图标在列表页里是内联 base64（没有 URL 可用），稀有度图标则是 fastcdn 上的 URL。
这里把 10 个属性图标按中文属性名落盘到 assets/elements/。
"""

import base64
import json
import os
import sys

from scrapling.fetchers import DynamicFetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch  # noqa: E402

URL = "https://baike.mihoyo.com/zzz/wiki/channel/map/2/43?mhy_presentation_style=fullscreen"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "elements")

page = DynamicFetcher.fetch(URL, headless=True, network_idle=True, load_dom=True, timeout=90000)

by_id = {c.content_id: c for c in fetch.fetch_via_api()}
rank_urls: dict[str, str] = {}
elements: dict[str, str] = {}

for a in page.css("a.position-list__list-card"):
    title = (a.attrib.get("title") or "").strip()
    href = a.attrib.get("href") or ""
    if not title or "/content/" not in href:
        continue
    cid = int(href.split("/content/")[1].split("/")[0])
    char = by_id.get(cid)
    if char is None:
        continue

    el = a.css(".element-subscript img")
    if el and char.element:
        src = el[0].attrib.get("src") or ""
        if src.startswith("data:"):
            elements[char.element] = src.split(",", 1)[1]

    rk = a.css(".rank-subscript img")
    if rk and char.rarity:
        rank_urls.setdefault(char.rarity, rk[0].attrib.get("src") or "")

os.makedirs(OUT, exist_ok=True)
for name, b64 in sorted(elements.items()):
    path = os.path.join(OUT, f"{name}.png")
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(b64))
    print(f"  {name}.png  {os.path.getsize(path)}B")

print(f"\n共 {len(elements)} 个属性图标 -> {OUT}")
print("\n稀有度图标 URL:")
for k, v in sorted(rank_urls.items()):
    print(f"  {k}: {v}")

missing = {c.element for c in by_id.values() if c.element} - set(elements)
print("\n没抽到的属性:", missing or "无")
