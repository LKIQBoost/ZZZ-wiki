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

# 属性没有现成的图标，用带色文字徽章代替
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

# 卡片右上角角标
CORNER_LABELS = {"Pre": "预告", "Encore": "复刻", "Forward": "前瞻"}


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
