"""把详情 JSON 里所有 URL 连同它的路径全挖出来，看有哪些图/视频可用。"""

import json
import os
import re
import sys

from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = (
    "https://act-api-takumi-static.mihoyo.com/hoyowiki/zzz/wapi/entry_page"
    "?app_sn=zzz_wiki&entry_page_id={cid}&lang=zh-cn"
)
HEADERS = {
    "x-rpc-wiki_app": "zzz",
    "Referer": "https://baike.mihoyo.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0.0.0 Safari/537.36",
}

URL_RE = re.compile(r"https?://[^\s\"'<>\\]+")

os.makedirs(".scratch", exist_ok=True)
payload = json.loads(Fetcher.get(API.format(cid=147), headers=HEADERS, timeout=40).body)
json.dump(payload, open(".scratch/147.json", "w", encoding="utf-8"), ensure_ascii=False)

found = []


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node[:40]):
            walk(v, f"{path}[{i}]")
    elif isinstance(node, str):
        for m in URL_RE.finditer(node):
            found.append((path, m.group(0)))
        # iframe / video src 之类
        for m in re.finditer(r'src="([^"]+)"', node):
            found.append((path + " <src>", m.group(1)))


page = payload["data"]["page"]
walk(page, "page")

# 去重但保留路径，方便看重复出现的
seen = {}
for path, url in found:
    seen.setdefault(url.split("?")[0], set()).add(path)

print(f"共 {len(found)} 处 URL，去重后 {len(seen)} 个\n")
kinds = {}
for url, paths in seen.items():
    ext = url.rsplit(".", 1)[-1].lower()
    kinds.setdefault(ext, []).append((url, sorted(paths)))

for ext, items in sorted(kinds.items()):
    print(f"===== .{ext}  ({len(items)}) =====")
    for url, paths in items[:6]:
        print(f"  {url[:110]}")
        for p in paths[:3]:
            print(f"      <- {p}")
    print()
