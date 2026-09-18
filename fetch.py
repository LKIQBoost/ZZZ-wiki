"""绝区零图鉴 · 代理人列表爬取。

图鉴页 (channel/map/2/43) 是 Nuxt 单页应用，角色卡片由 XHR 渲染。
主路径直接请求前端同款接口，字段最全（含 属性/特性/阵营/稀有度）；
接口不可用时回退到 DynamicFetcher 渲染 DOM，此时只能拿到
名字、图标与 content_id，属性类字段为 None。

    uv run python fetch.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scrapling.fetchers import DynamicFetcher, Fetcher

APP_SN = "zzz_wiki"
CHANNEL_ID = 43  # 游戏图鉴 > 代理人

API_URL = (
    "https://api-takumi-static.mihoyo.com/common/blackboard"
    f"/{APP_SN}/v1/home/content/list?app_sn={APP_SN}&channel_id={CHANNEL_ID}"
)
MAP_URL = f"https://baike.mihoyo.com/zzz/wiki/channel/map/2/{CHANNEL_ID}"
DETAIL_URL = (
    "https://baike.mihoyo.com/zzz/wiki/content/{content_id}/detail"
    "?mhy_presentation_style=fullscreen"
)

# 接口 ext 里的标签前缀 -> Character 字段名，其余前缀归入 tags
TAG_FIELDS = {"属性": "element", "特性": "specialty", "阵营": "faction", "稀有度": "rarity"}

log = logging.getLogger("zzz.fetch")


@dataclass
class Character:
    """一个代理人。"""

    content_id: int
    name: str  # 全名，如「赛维里安·洛威尔」
    short_name: str = ""  # 简称，如「赛维里安」
    icon: str = ""
    element: str | None = None  # 属性
    specialty: str | None = None  # 特性
    faction: str | None = None  # 阵营
    rarity: str | None = None  # 稀有度 S/A
    corner_mark: str | None = None  # 角标：Pre / Encore / Forward
    tags: list[str] = field(default_factory=list)  # 未归类的原始标签

    @property
    def detail_url(self) -> str:
        return DETAIL_URL.format(content_id=self.content_id)

    def __str__(self) -> str:
        bits = " ".join(x for x in (self.rarity, self.element, self.specialty) if x)
        return f"{self.name:<16} {bits:<12} {self.faction or ''}"


def _clean(value: object) -> str | None:
    """接口里空值既可能是 "" 也可能是字符串 "None"，统一成 None。"""
    text = str(value or "").strip()
    return text if text and text != "None" else None


def parse_tags(ext_raw: str) -> dict[str, list[str]]:
    """把条目里的 ext 字段拆成 {"属性": ["风"], "特性": ["强攻"], ...}。

    ext 形如 {"c_43": {"filter": {"text": "[\"属性/风\",\"特性/强攻\"]"}}}，
    其中 text 本身是一层被转义的 JSON 字符串。
    """
    result: dict[str, list[str]] = {}
    if not ext_raw:
        return result

    ext = json.loads(ext_raw)
    for channel in ext.values():
        if not isinstance(channel, dict):
            continue
        text = (channel.get("filter") or {}).get("text")
        if not text:
            continue
        for tag in json.loads(text):
            category, sep, value = tag.partition("/")
            if not sep:
                category, value = "其他", tag
            result.setdefault(category, []).append(value)
    return result


def character_from_entry(entry: dict) -> Character:
    """把接口返回的一个 list 条目转成 Character。"""
    tags = parse_tags(entry.get("ext") or "")
    extra = {v for k, vs in tags.items() if k not in TAG_FIELDS for v in vs}
    return Character(
        content_id=int(entry["content_id"]),
        name=(entry.get("title") or "").strip(),
        short_name=(entry.get("alias_name") or "").strip(),
        icon=entry.get("icon") or "",
        corner_mark=_clean(entry.get("corner_mark")),
        tags=sorted(extra),
        **{f: (tags.get(k) or [None])[0] for k, f in TAG_FIELDS.items()},
    )


def fetch_via_api(timeout: int = 30) -> list[Character]:
    """主路径：请求前端同款接口。"""
    resp = Fetcher.get(API_URL, timeout=timeout)
    if resp.status != 200:
        raise RuntimeError(f"接口返回 HTTP {resp.status}")

    payload = json.loads(resp.body)
    if payload.get("retcode") != 0:
        raise RuntimeError(f"接口返回 retcode={payload.get('retcode')} {payload.get('message')}")

    # data.list 里找到 channel_id 对应的那一项，角色在它的 list 里
    for node in payload["data"]["list"]:
        if node.get("id") == CHANNEL_ID:
            entries = node.get("list") or []
            break
    else:
        raise RuntimeError(f"接口响应里没有 channel_id={CHANNEL_ID}")

    if not entries:
        raise RuntimeError("接口返回的代理人列表为空")
    return [character_from_entry(e) for e in entries]


def fetch_via_dom(timeout: int = 60000) -> list[Character]:
    """兜底路径：渲染页面后从卡片里取链接与名字。

    注意卡片本身不带属性信息（属性/稀有度在 DOM 里是 base64 图片），
    所以这几个字段会是 None。
    """
    page = DynamicFetcher.fetch(
        MAP_URL,
        headless=True,
        network_idle=True,
        load_dom=True,
        timeout=timeout,
    )

    characters: list[Character] = []
    for card in page.css("a.position-list__list-card"):
        href = card.attrib.get("href") or ""
        match = re.search(r"/content/(\d+)/detail", href)
        name = (card.attrib.get("title") or "").strip()
        if not match or not name:
            continue  # 列表尾部的空占位卡片

        icon = (
            card.css(".agent-card__img img::attr(data-src)").get()
            or card.css(".agent-card__img img::attr(src)").get()
            or ""
        )
        characters.append(
            Character(
                content_id=int(match.group(1)),
                name=name,
                short_name=(card.css(".agent-card__name::text").get() or "").strip(),
                # 缩略图带 oss 缩放参数，去掉后是原图
                icon=icon.split("?")[0],
            )
        )
    return characters


def fetch_characters() -> list[Character]:
    """抓全部代理人，接口优先、DOM 兜底。"""
    try:
        characters = fetch_via_api()
        log.info("接口抓取成功：%d 个代理人", len(characters))
        return characters
    except Exception as exc:
        log.warning("接口抓取失败（%s），回退到渲染 DOM", exc)

    characters = fetch_via_dom()
    log.info("DOM 抓取成功：%d 个代理人", len(characters))
    return characters


def main() -> None:
    # Windows 控制台默认不是 UTF-8，中文会炸
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("scrapling").setLevel(logging.WARNING)  # 关掉每请求一行的 INFO

    characters = fetch_characters()
    for c in characters:
        print(c)
    print(f"\n共 {len(characters)} 个代理人")

    records = [{**asdict(c), "detail_url": c.detail_url} for c in characters]
    out = Path(__file__).with_name("agents.json")
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out}")


if __name__ == "__main__":
    main()
