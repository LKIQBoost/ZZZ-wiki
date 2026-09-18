"""配色与通用组件，照着米游社百科那套暗色 + 金色的风格。"""

from __future__ import annotations

import flet as ft

BG = "#151517"  # 页面底色
CARD = "#1F1F23"  # 内容卡片
CARD_HI = "#2A2A30"  # 次级卡片 / 徽章底
LINE = "#33333A"  # 分隔线
ACCENT = "#FFD24C"  # 官网那抹金色
TEXT = "#F2F2F3"
TEXT_DIM = "#8B8B95"

RARITY_COLORS = {"S": "#FFB13D", "A": "#B98BE0"}

# 稀有度徽章官网用的是 fastcdn 上的图标
RARITY_ICONS = {
    "S": "https://fastcdn.mihoyo.com/static-resource-v2/2024/05/15/"
    "809ad658ea69bb370ba145e37091505a_2903902069612010924.png",
    "A": "https://fastcdn.mihoyo.com/static-resource-v2/2024/05/15/"
    "9c4f034e428e25f88bb3daddfdd89f64_8563435929380171954.png",
}

# 属性图标在官网是内联 base64，没有 URL，已抽成 assets/elements/<enum>.png
# 文件名用接口里的英文枚举，避开中文路径
ELEMENT_ASSETS = {
    "电": "electric",
    "火": "fire",
    "冰": "ice",
    "物理": "physical",
    "以太": "ether",
    "风": "wind",
    "烈霜": "frost",
    "玄墨": "auricink",
    "凛刃": "honed_edge",
    "流明": "lumiflux",
}

# 图标取不到时退回带色文字
ELEMENT_COLORS = {
    "电": "#4FC1F0",
    "火": "#FF6B4A",
    "冰": "#7FD6F5",
    "物理": "#D8D8DC",
    "以太": "#C77DFF",
    "风": "#6FD08C",
    "烈霜": "#A8E6F0",
    "玄墨": "#8D9AA5",
    "凛刃": "#FFA23D",
    "流明": "#FFE873",
}


def element_src(element: str | None) -> str | None:
    asset = ELEMENT_ASSETS.get(element or "")
    return f"elements/{asset}.png" if asset else None

# 卡片右上角角标
CORNER_LABELS = {"Pre": "预告", "Encore": "复刻", "Forward": "前瞻"}


def blend(color: str | None, base: str = BG, ratio: float = 0.28) -> str:
    """把 color 按比例混进 base，用来做头图渐变。

    官网头图是角色主题色（bg_rolling_color）铺的大色块，直接拿来当背景
    会太亮压住文字，所以先往深色底里兑一下。
    """
    if not color or not color.startswith("#") or len(color) != 7:
        return CARD

    def rgb(value: str) -> tuple[int, int, int]:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]

    try:
        r1, g1, b1 = rgb(color)
        r2, g2, b2 = rgb(base)
    except ValueError:
        return CARD

    mix = lambda a, b: int(a * ratio + b * (1 - ratio))  # noqa: E731
    return f"#{mix(r1, r2):02X}{mix(g1, g2):02X}{mix(b1, b2):02X}"


def thumbnail(url: str, size: int) -> str:
    """给米游社 OSS 图加缩放参数，列表页别去拉原图。"""
    if not url:
        return ""
    if "act-upload.mihoyo.com" not in url:
        return url
    return f"{url.split('?')[0]}?x-oss-process=image/quality,q_75/resize,s_{size}/format,webp"


def badge(text: str, color: str, *, size: int = 12) -> ft.Control:
    """左上角那种小方块徽章。"""
    return ft.Container(
        bgcolor=color,
        border_radius=3,
        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        content=ft.Text(text, size=size, weight=ft.FontWeight.BOLD, color="#1A1A1A"),
    )


def icon_badge(
    src: str | None,
    *,
    size: int = 26,
    fallback: ft.Control | None = None,
) -> ft.Control:
    """官网那种图形徽章；图片取不到时退回传进来的文字徽章。"""
    if not src:
        return fallback if fallback is not None else ft.Container()
    return ft.Image(
        src=src,
        width=size,
        height=size,
        fit=ft.BoxFit.CONTAIN,
        error_content=fallback,
    )


def section(title: str, *controls: ft.Control, trailing: ft.Control | None = None) -> ft.Control:
    """官网那种带标题条的内容卡片。"""
    heading: list[ft.Control] = [
        ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=TEXT)
    ]
    if trailing is not None:
        heading.append(trailing)

    return ft.Container(
        bgcolor=CARD,
        border_radius=8,
        content=ft.Column(
            [
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    border=ft.Border.only(bottom=ft.BorderSide(1, LINE)),
                    content=ft.Row(heading, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ),
                ft.Container(
                    padding=16,
                    content=ft.Column(
                        list(controls),
                        spacing=10,
                        # Column 默认是 START，子项会缩成内容宽度，撑不满卡片
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                ),
            ],
            spacing=0,
        ),
    )


def info_pill(label: str, value: str | None) -> ft.Control:
    """详情页那排「属性 ｜ 电」的小格子。"""
    return ft.Container(
        bgcolor=CARD_HI,
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        expand=True,
        content=ft.Row(
            [
                ft.Text(label, size=13, color=TEXT_DIM),
                ft.Text(value or "—", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )


def chip(text: str) -> ft.Control:
    return ft.Container(
        bgcolor=CARD_HI,
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        content=ft.Text(text, size=12, color=ACCENT),
    )


def body_text(text: str) -> ft.Control:
    """大段正文，行距放宽一点好读。"""
    return ft.Text(text, size=13, color=TEXT, selectable=True)
