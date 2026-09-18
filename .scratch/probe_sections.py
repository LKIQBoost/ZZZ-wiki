"""看全部 62 个详情页的 module 结构，确认怎么区分「意象影画」和「角色展示」。"""

import collections
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from scrapling.fetchers import Fetcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch  # noqa: E402

API = (
    "https://act-api-takumi-static.mihoyo.com/hoyowiki/zzz/wapi/entry_page"
    "?app_sn=zzz_wiki&entry_page_id={cid}&lang=zh-cn"
)
HEADERS = {
    "x-rpc-wiki_app": "zzz",
    "Referer": "https://baike.mihoyo.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0.0.0 Safari/537.36",
}
os.makedirs(".scratch/details", exist_ok=True)

chars = fetch.fetch_via_api()


def grab(c):
    r = Fetcher.get(API.format(cid=c.content_id), headers=HEADERS, timeout=40)
    json.dump(json.loads(r.body), open(f".scratch/details/{c.content_id}.json", "w", encoding="utf-8"), ensure_ascii=False)
    return c


with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(grab, chars))
print("已抓", len(chars))

combo = collections.Counter()
tabs_by_cid = {}
for c in chars:
    pg = json.load(open(f".scratch/details/{c.content_id}.json", encoding="utf-8"))["data"]["page"]
    per = []
    for m in pg.get("modules") or []:
        for comp in m.get("components") or []:
            cid = comp.get("component_id")
            d = comp.get("data")
            if isinstance(d, str):
                d = json.loads(d)
            if cid == "map_desc":
                tabs = tuple(it.get("tab_name") for it in (d.get("list") or []))
                per.append(("map_desc", tabs))
    tabs_by_cid[c.content_id] = per

alltabs = collections.Counter()
for cid, per in tabs_by_cid.items():
    for kind, tabs in per:
        for t in tabs:
            alltabs[t] += 1

print(f"\n=== 所有 map_desc 的 tab_name（{len(alltabs)} 种）===")
for t, n in alltabs.most_common():
    print(f"  {n:>3}  {t!r}")

print("\n=== 每个角色的 map_desc 组数分布 ===")
print(collections.Counter(len(v) for v in tabs_by_cid.values()))
