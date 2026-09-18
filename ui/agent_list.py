"""代理人列表页：筛选栏 + 头像卡片网格。"""

from __future__ import annotations

import flet as ft

from fetch import Character

from . import theme as t

ALL = "全部"

# 筛选栏的显示名 -> Character 字段名
FILTER_FIELDS = {
    "稀有度": "rarity",
    "属性": "element",
    "特性": "specialty",
    "阵营": "faction",
}


class AgentListView:
    """卡片网格。数据由外部抓好后调 set_characters 灌进来。"""

    def __init__(self, page: ft.Page, on_select) -> None:
        self.page = page
        self.on_select = on_select
        self.characters: list[Character] = []
        self.selected: dict[str, str] = {label: ALL for label in FILTER_FIELDS}

        self.title = ft.Text("代理人", size=22, weight=ft.FontWeight.BOLD, color=t.TEXT)
        self.count = ft.Text("", size=13, color=t.TEXT_DIM)
        self.filters_row = ft.Row(wrap=True, spacing=10)
        self.grid = ft.GridView(
            expand=True,
            max_extent=168,
            child_aspect_ratio=0.78,
            spacing=12,
            run_spacing=12,
        )
        self.status = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Text("", size=13, color=t.TEXT_DIM),
        )

        self.body = ft.Container(content=self.status, expand=True)
        self.root = ft.Column(
            [
                ft.Row(
                    [self.title, self.count],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self.filters_row,
                self.body,
            ],
            expand=True,
            spacing=14,
        )

    # ---- 状态切换 ----

    def show_loading(self) -> None:
        self.status.content = ft.Column(
            [
                ft.ProgressRing(color=t.ACCENT, width=28, height=28),
                ft.Text("正在获取代理人列表…", size=13, color=t.TEXT_DIM),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            tight=True,
        )
        self.body.content = self.status
        self.filters_row.controls = []
        self.count.value = ""

    def show_error(self, message: str) -> None:
        self.status.content = ft.Column(
            [
                ft.Icon(ft.Icons.WIFI_OFF, size=32, color=t.TEXT_DIM),
                ft.Text("列表获取失败", size=15, color=t.TEXT),
                ft.Text(message, size=12, color=t.TEXT_DIM, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            tight=True,
        )
        self.body.content = self.status

    def set_characters(self, characters: list[Character]) -> None:
        self.characters = characters
        self._build_filters()
        self.body.content = self.grid
        self._refresh_grid()

    # ---- 筛选 ----

    def _build_filters(self) -> None:
        self.filters_row.controls = [
            self._dropdown(label, field) for label, field in FILTER_FIELDS.items()
        ]

    def _dropdown(self, label: str, field: str) -> ft.Control:
        values = sorted({getattr(c, field) for c in self.characters if getattr(c, field)})
        return ft.Dropdown(
            label=label,
            value=self.selected[label],
            width=150,
            text_size=13,
            label_style=ft.TextStyle(size=12, color=t.TEXT_DIM),
            options=[ft.DropdownOption(key=ALL, text=ALL)]
            + [ft.DropdownOption(key=v, text=v) for v in values],
            on_select=lambda e, lb=label: self._on_filter(lb, e.control.value),
        )

    def _on_filter(self, label: str, value: str) -> None:
        self.selected[label] = value
        self._refresh_grid()
        self.page.update()

    def _visible(self) -> list[Character]:
        result = self.characters
        for label, field in FILTER_FIELDS.items():
            wanted = self.selected[label]
            if wanted != ALL:
                result = [c for c in result if getattr(c, field) == wanted]
        return result

    def _refresh_grid(self) -> None:
        shown = self._visible()
        self.grid.controls = [self._card(c) for c in shown]
        self.count.value = f"{len(shown)} / {len(self.characters)}"

    # ---- 卡片 ----

    def _card(self, character: Character) -> ft.Control:
        top_left: list[ft.Control] = []
        if character.rarity:
            top_left.append(
                t.icon_badge(
                    t.RARITY_ICONS.get(character.rarity),
                    size=24,
                    fallback=t.badge(
                        character.rarity,
                        t.RARITY_COLORS.get(character.rarity, t.ACCENT),
                    ),
                )
            )
        if character.element:
            top_left.append(
                t.icon_badge(
                    t.element_src(character.element),
                    size=24,
                    fallback=t.badge(
                        character.element,
                        t.ELEMENT_COLORS.get(character.element, t.TEXT_DIM),
                    ),
                )
            )

        layers: list[ft.Control] = []
        if character.icon:
            layers.append(
                ft.Image(
                    src=t.thumbnail(character.icon, 278),
                    fit=ft.BoxFit.COVER,
                    expand=True,
                )
            )
        else:
            layers.append(ft.Container(expand=True))

        if top_left:
            layers.append(
                ft.Container(
                    left=7,
                    top=7,
                    content=ft.Column(top_left, spacing=4, tight=True),
                )
            )

        corner = t.CORNER_LABELS.get(character.corner_mark or "")
        if corner:
            layers.append(
                ft.Container(
                    right=7,
                    top=7,
                    content=t.badge(corner, t.ACCENT, size=11),
                )
            )

        name = character.short_name or character.name
        layers.append(
            ft.Container(
                left=0,
                right=0,
                bottom=0,
                bgcolor="#B3000000",
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                content=ft.Text(
                    name,
                    size=12,
                    color=t.TEXT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            )
        )

        return ft.Container(
            bgcolor=t.CARD,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            tooltip=character.name,
            on_click=lambda e, c=character: self.on_select(c),
            content=ft.Stack(layers, expand=True),
        )
