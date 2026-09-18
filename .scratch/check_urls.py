"""抽样验证新增的媒体 URL 真的能取到图。"""

import collections
import json
from concurrent.futures import ThreadPoolExecutor

import httpx

d = json.load(open("details.json", encoding="utf-8"))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153.0.0.0 Safari/537.36"}

urls: dict[str, set[str]] = collections.defaultdict(set)
for c in d:
    if c["portrait"]:
        urls["portrait"].add(c["portrait"])
    if c["faction_icon"]:
        urls["faction_icon"].add(c["faction_icon"])
    for m in c["cinema"][:2]:
        urls["cinema"].add(m["image"])
    for m in c["showcase"][:2]:
        urls["showcase"].add(m["image"])
    for m in c["gallery"][:1]:
        urls["gallery"].add(m["image"])
    for g in c["skills"][:2]:
        for s in g["skills"][:2]:
            if s["icon"]:
                urls["skill_gif"].add(s["icon"])
    for s in c["strategies"][:1]:
        if s["cover"]:
            urls["strategy"].add(s["cover"])

sample = []
for kind, group in urls.items():
    for u in sorted(group)[:10]:
        sample.append((kind, u))

print(f"总 URL 数 {sum(len(v) for v in urls.values())}，抽样 {len(sample)} 个\n")


def check(item):
    kind, url = item
    try:
        # HEAD 就够判断链接死没死，动图动辄几 MB，别真下
        r = httpx.head(url, headers=UA, timeout=20, follow_redirects=True)
        return kind, r.status_code, r.headers.get("content-type", "")[:30], 0, url
    except Exception as exc:
        return kind, "ERR", str(exc)[:40], 0, url


results = list(ThreadPoolExecutor(max_workers=6).map(check, sample))

stat = collections.Counter((k, s) for k, s, *_ in results)
for (kind, status), n in sorted(stat.items(), key=lambda x: str(x[0])):
    flag = "OK " if status == 200 else "!! "
    print(f"{flag}{kind:<12} status={status}  x{n}")

bad = [r for r in results if r[1] != 200]
print(f"\n失败 {len(bad)} 个")
for kind, status, ct, size, url in bad[:8]:
    print(f"  {kind} {status} {ct} {url[:100]}")
