"""绝区零图鉴 · 代理人详情爬取。

详情页也是 Nuxt 渲染的，数据来自 hoyowiki 的 entry_page 接口。
接口必须带 x-rpc-wiki_app 头，否则一律返回 retcode=404（「信号好像消失了」）。

    uv run python detail.py        # 抓全部代理人详情，写 details.json
"""

from __future__ import annotations

import html
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scrapling.fetchers import Fetcher

from fetch import APP_SN, DETAIL_URL, fetch_characters

log = logging.getLogger("zzz.detail")

DETAIL_API = "https://act-api-takumi-static.mihoyo.com/hoyowiki/zzz/wapi/entry_page"

HEADERS = {
    # 缺这个头接口会假装词条不存在
    "x-rpc-wiki_app": "zzz",
    "Referer": "https://baike.mihoyo.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
    ),
}

# role_base_info 里是英文枚举，映射成图鉴上的中文写法
ELEMENTS = {
    "electric": "电",
    "fire": "火",
    "ice": "冰",
    "physical": "物理",
    "ether": "以太",
    "wind": "风",
    "frost": "烈霜",
    "auricink": "玄墨",
    "honed_edge": "凛刃",
    "Lumiflux": "流明",
}
SPECIALTIES = {
    "strike": "强攻",
    "abnormal": "异常",
    "pierce": "击破",
    "support": "支援",
    "guard": "防护",
    "rupture": "命破",
    "armero": "锋御",
}
# CV 面板有「中配」和「中文CV」两种写法
CV_LABELS = {
    "中配": "中配",
    "中文CV": "中配",
    "日配": "日配",
    "日文CV": "日配",
    "英配": "英配",
    "英文CV": "英配",
    "韩配": "韩配",
    "韩文CV": "韩配",
}

_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Skill:
    name: str
    desc: str


@dataclass
class SkillGroup:
    """一组技能，如「普攻」「特殊技」。"""

    name: str
    skills: list[Skill] = field(default_factory=list)


@dataclass
class CharacterDetail:
    content_id: int
    name: str
    alias_name: str = ""
    rarity: str | None = None  # S / A，未上线角色没有
    element: str | None = None  # 属性
    specialty: str | None = None  # 特性
    faction: str | None = None  # 阵营，取自列表接口（见 fetch_all_details）
    subtitle: str | None = None  # 详情页名字下的那行，多数是阵营，少数是称号
    birthday: str | None = None
    height: str | None = None
    romanized: str | None = None  # 立绘上的罗马音，如 ANTON IVANOV
    portrait: str | None = None  # 立绘
    tags: list[str] = field(default_factory=list)  # 【角色TAG】
    intro: str = ""  # 【角色详情】
    cv: dict[str, str] = field(default_factory=dict)  # 中配/日配/英配/韩配
    impression: str = ""  # 角色印象
    story: str = ""  # 角色故事
    store_message: str = ""  # 录像店经营留言信息
    skills: list[SkillGroup] = field(default_factory=list)
    source_url: str = ""

    def __str__(self) -> str:
        bits = " ".join(x for x in (self.rarity, self.element, self.specialty) if x)
        return f"{self.name:<16} {bits:<12} 技能 {len(self.skills)} 组  {self.faction or ''}"


def html_to_text(raw: str) -> str:
    """把接口里的富文本 HTML 压成纯文本，块级标签转成换行。"""
    if not raw:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    text = re.sub(r"</(p|div|h\d|li)>", "\n", text, flags=re.I)
    text = _TAG_RE.sub("", text)
    return html.unescape(text).strip()


def html_to_lines(raw: str) -> list[str]:
    return [line.strip() for line in html_to_text(raw).splitlines() if line.strip()]


def _iter_components(page: dict):
    """遍历所有 module 里的 component，产出 (module 名, component_id, data)。"""
    for module in page.get("modules") or []:
        for comp in module.get("components") or []:
            data = comp.get("data")
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    continue
            if isinstance(data, dict):
                yield module.get("name") or "", comp.get("component_id"), data


def _parse_intro(raw: str) -> tuple[list[str], str]:
    """从 rich_row_base_info 里拆出【角色TAG】与【角色详情】。"""
    text = html_to_text(raw)

    tags: list[str] = []
    match = re.search(r"【角色TAG】\s*([^\n]*)", text)
    if match:
        tags = [t.strip() for t in re.split(r"[、,，]", match.group(1)) if t.strip()]

    match = re.search(r"【角色详情】\s*(.*)", text, re.S)
    # 没有【角色详情】标记时，去掉 TAG 那行后整段当简介
    intro = match.group(1) if match else re.sub(r"【角色TAG】[^\n]*", "", text)
    return tags, intro.strip()


def _parse_cv(raw: str) -> dict[str, str]:
    cv: dict[str, str] = {}
    for line in html_to_lines(raw):
        match = re.match(r"^([^：:]{1,10})[：:]\s*(.*)$", line)
        if not match:
            continue
        label = CV_LABELS.get(match.group(1).strip())
        if label:
            cv[label] = match.group(2).strip()
    return cv


def _parse_skills(data: dict) -> list[SkillGroup]:
    """role_talent 会出现两次：一次是技能，一次是养成材料。

    两者靠 tab_name 区分——养成材料那组的 tab_name 是「总计」。
    技能组的 title 常常是空的，这时退回用 tab_name 当组名。
    """
    groups: list[SkillGroup] = []
    for item in data.get("list") or []:
        tab_name = (item.get("tab_name") or "").strip()
        if not tab_name or tab_name == "总计":
            continue

        name = (item.get("title") or "").strip() or tab_name
        skills = [
            Skill(
                name=(child.get("title") or "").strip(),
                desc=html_to_text(child.get("desc") or ""),
            )
            for child in item.get("children") or []
            if (child.get("title") or "").strip()
        ]
        # 少数招式组没有子条目，组自身的 desc 就是全部内容
        if not skills and (item.get("desc") or "").strip():
            skills = [Skill(name=name, desc=html_to_text(item["desc"]))]

        groups.append(SkillGroup(name=name, skills=skills))
    return groups


def parse_detail(payload: dict) -> CharacterDetail:
    """把 entry_page 接口的响应转成 CharacterDetail。"""
    page = payload["data"]["page"]

    detail = CharacterDetail(
        content_id=int(page["id"]),
        name=page.get("name") or "",
        alias_name=page.get("alias_name") or "",
        source_url=DETAIL_URL.format(content_id=page["id"]),
    )

    for module_name, component_id, data in _iter_components(page):
        if component_id == "role_base_info":
            detail.rarity = data.get("grade") or detail.rarity
            detail.element = ELEMENTS.get(data.get("role_attribute"), detail.element)
            detail.specialty = SPECIALTIES.get(data.get("role_profession"), detail.specialty)
            detail.subtitle = (data.get("addition_text") or "").strip() or detail.subtitle
            detail.romanized = (data.get("bg_rolling_text") or "").strip() or detail.romanized
            detail.portrait = data.get("tachie_pc") or detail.portrait
            for entry in data.get("custom_field") or []:
                key, value = entry.get("key"), (entry.get("value") or "").strip()
                if key == "出生日期":
                    detail.birthday = value
                elif key == "身高":
                    detail.height = value

        elif component_id == "rich_row_base_info":
            detail.tags, detail.intro = _parse_intro(data.get("rich_text") or "")

        elif component_id == "collapse_panel":
            text = html_to_text(data.get("rich_text") or "")
            if module_name == "角色印象":
                detail.impression = text
            elif module_name == "角色故事":
                detail.story = text
            elif module_name == "录像店经营留言信息":
                detail.store_message = text
            elif "CV" in module_name:
                detail.cv = _parse_cv(data.get("rich_text") or "")

        elif component_id == "role_talent":
            detail.skills.extend(_parse_skills(data))

    return detail


def fetch_detail(content_id: int, timeout: int = 30) -> CharacterDetail:
    """抓单个代理人详情。"""
    url = f"{DETAIL_API}?app_sn={APP_SN}&entry_page_id={content_id}&lang=zh-cn"
    resp = Fetcher.get(url, headers=HEADERS, timeout=timeout)
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}")

    payload = json.loads(resp.body)
    if payload.get("retcode") != 0 or not payload.get("data"):
        raise RuntimeError(f"retcode={payload.get('retcode')} {payload.get('message')}")
    return parse_detail(payload)


def fetch_all_details(characters=None) -> list[CharacterDetail]:
    """抓全部代理人详情，单个失败跳过不影响整体。

    详情页的 addition_text 有时是阵营、有时是称号（如「虚狩·青溟司命」），
    所以阵营一律用列表接口的值覆盖，详情页那行单独存进 subtitle。
    """
    characters = characters or fetch_characters()
    details: list[CharacterDetail] = []
    total = len(characters)

    for index, character in enumerate(characters, 1):
        try:
            detail = fetch_detail(character.content_id)
        except Exception as exc:
            log.warning("[%d/%d] %s 失败：%s", index, total, character.name, exc)
            continue
        detail.faction = character.faction
        details.append(detail)
        print(f"[{index}/{total}] {detail}")

    return details


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("scrapling").setLevel(logging.WARNING)  # 关掉每请求一行的 INFO

    details = fetch_all_details()
    print(f"\n共 {len(details)} 份详情")

    out = Path(__file__).with_name("details.json")
    out.write_text(
        json.dumps([asdict(d) for d in details], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已写入 {out}")


if __name__ == "__main__":
    main()
