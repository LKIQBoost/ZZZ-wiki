"""统计列表卡片上的徽章图标：稀有度是 URL，属性/角标是 base64 还是 URL。"""

import base64
import collections
import hashlib
import json
import os
import re

from scrapling.fetchers import DynamicFetcher

URL = "https://baike.mihoyo.com/zzz/wiki/channel/map/2/43?mhy_presentation_style=fullscreen"
page = DynamicFetcher.fetch(
    URL, headless=True, network_idle=True, load_dom=True, timeout=90000
)

cards = [a for a in page.css("a.position-list__list-card") if (a.attrib.get("title") or "").strip()]

rank, element, corner = {}, {}, collections.Counter()

for a in cards:
    name = a.attrib.get("title")

    def get(sel):
        el = a.css(f"{sel} img")
        return el[0].attrib.get("src") if el else None

    r = get(".rank-subscript")
    e = get(".element-subscript")
    c = get(".agent-card__corner")
    rank.setdefault(r, []).append(name)
    element.setdefault(e, []).append(name)
    if c:
        corner[c[:40]] += 1

print("=== 稀有度图标 ===")
for src, names in rank.items():
    print(f"  {len(names):>2} 人  {str(src)[:110]}")
    print(f"         例: {names[:4]}")

print("\n=== 属性图标（看是 base64 还是 URL）===")
for src, names in element.items():
    kind = "BASE64" if str(src).startswith("data:") else "URL"
    print(f"  {len(names):>2} 人  [{kind}] {str(src)[:90]}")
    print(f"         例: {names[:4]}")

print(f"\n=== 角标出现次数: {sum(corner.values())} ===")
for k, n in corner.most_common(6):
    print(f"  {n:>2}  {k}")

# 把 base64 的都存下来看看大小和种类
os.makedirs(".scratch/icons", exist_ok=True)
saved = []
for src, names in element.items():
    if str(src).startswith("data:"):
        data = base64.b64decode(src.split(",", 1)[1])
        h = hashlib.md5(data).hexdigest()[:10]
        saved.append((h, len(data), names))
        open(f".scratch/icons/{h}.png", "wb").write(data)
print("\n=== 属性图标落盘 ===")
for h, size, names in saved:
    print(f"  {h}.png  {size:>6}B  {names[0]} 等 {len(names)} 人")
