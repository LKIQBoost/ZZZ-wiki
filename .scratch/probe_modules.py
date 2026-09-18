"""逐个 module 看媒体字段：技能图标、阵营图标、影画图、角色展示图/视频。"""

import json
import re

raw = open(".scratch/147.json", encoding="utf-8").read()
pg = json.loads(raw)["data"]["page"]

print("=== 有没有视频相关字段 ===")
for kw in ["mp4", "video", "iframe", "bilibili", ".m3u8", "media"]:
    hits = re.findall(rf'"[^"]*{kw}[^"]*"', raw, re.I)[:4]
    print(f"  {kw}: {len(re.findall(kw, raw, re.I))} -> {hits[:3]}")


def comps(m):
    for c in m.get("components") or []:
        d = c.get("data")
        if isinstance(d, str):
            d = json.loads(d)
        yield c.get("component_id"), d


for mi, m in enumerate(pg["modules"]):
    for cid, d in comps(m):
        print(f"\n--- module[{mi}] {cid} name={m.get('name')!r}")
        if cid == "role_base_info":
            for k in ("role_faction", "addition_img", "tachie_pc", "tachie_m", "bg_pc", "bg_m", "bg_rolling_color", "addition_text"):
                print(f"    {k}: {str(d.get(k))[:95]}")
        elif cid == "role_talent":
            for t in (d.get("list") or [])[:2]:
                print(f"    组 title={t.get('title')!r} icon={str(t.get('icon'))[:70]}")
                for ch in (t.get("children") or [])[:2]:
                    print(f"      招式 {ch.get('title')!r}")
                    print(f"         icon={str(ch.get('icon'))[:75]}")
                    print(f"         animated={str(ch.get('animated_icon'))[:75]}")
        elif cid == "double_col_table":
            for t in d.get("tables") or []:
                print(f"    header={t.get('header')}")
                row = (t.get("row") or [[]])[0]
                for cell in row:
                    imgs = re.findall(r'src="([^"]+)"', str(cell))
                    print(f"     cell imgs={len(imgs)} {[u[:70] for u in imgs[:2]]}")
        elif cid == "map_desc":
            for it in (d.get("list") or [])[:4]:
                print(f"    item keys={list(it)} tab={it.get('tab_name')!r} image={str(it.get('image'))[:85]}")
            print(f"    tachieImage={str(d.get('tachieImage'))[:85]}")
        elif cid == "strategy":
            for it in (d.get("list") or [])[:3]:
                print(f"    {list(it)} cover={str(it.get('cover'))[:80]} link={str(it.get('link'))[:60]}")
