"""代理人详情页：立绘头图 + 分节内容，照着官网那套版式。"""

from __future__ import annotations

import flet as ft

from detail import CharacterDetail

from . import theme as t

CV_ORDER = ("中配", "日配", "英配", "韩配")


class AgentDetailView:
    """详情展示。数据由外部抓好后调 show_detail 灌进来。"""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.body = ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.root = ft.Column(
            [self.body],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ---- 状态 ----

    def show_empty(self) -> None:
        self._set(
            self._placeholder(
                ft.Icons.PERSON_SEARCH,
                "还没有选择代理人",
                "到「代理人」页点一个角色，这里会加载它的详情。",
            )
        )

    def show_loading(self, name: str) -> None:
        self._set(
            self._placeholder(
                None,
                f"正在加载「{name}」…",
                "详情页首次点开才会去抓，稍等一下。",
                loading=True,
            )
        )

    def show_error(self, name: str, message: str) -> None:
        self._set(
            self._placeholder(ft.Icons.ERROR_OUTLINE, f"「{name}」加载失败", message)
        )

    def _placeholder(self, icon, title: str, hint: str, loading: bool = False):
        head = (
            ft.ProgressRing(color=t.ACCENT, width=28, height=28)
            if loading
            else ft.Icon(icon, size=34, color=t.TEXT_DIM)
        )
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=140),
            content=ft.Column(
                [
                    head,
                    ft.Text(title, size=15, color=t.TEXT),
                    ft.Text(hint, size=12, color=t.TEXT_DIM, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                tight=True,
            ),
        )

    def _set(self, control: ft.Control) -> None:
        self.body.controls = [control]

    # ---- 详情 ----

    def show_detail(self, detail: CharacterDetail) -> None:
        sections: list[ft.Control] = [self._hero(detail)]

        if detail.tags or detail.intro:
            body: list[ft.Control] = []
            if detail.tags:
                body.append(ft.Row([t.chip(x) for x in detail.tags], wrap=True, spacing=8))
            if detail.intro:
                body.append(t.body_text(detail.intro))
            sections.append(t.section("角色介绍", *body))

        if detail.cv:
            rows = [
                ft.Row(
                    [
                        ft.Text(label, size=13, color=t.TEXT_DIM, width=60),
                        ft.Text(detail.cv[label], size=13, color=t.TEXT, selectable=True),
                    ],
                    spacing=12,
                )
                for label in CV_ORDER
                if label in detail.cv
            ]
            sections.append(t.section("角色CV", *rows))

        if detail.skills:
            sections.append(t.section("技能展示", *self._skills(detail)))

        for title, text in (
            ("角色印象", detail.impression),
            ("角色故事", detail.story),
            ("录像店经营留言信息", detail.store_message),
        ):
            if text:
                sections.append(t.section(title, t.body_text(text)))

        if detail.source_url:
            sections.append(
                ft.Text(
                    f"数据来源：{detail.source_url}",
                    size=11,
                    color=t.TEXT_DIM,
                    selectable=True,
                )
            )

        self._set(ft.Column(sections, spacing=14))

    def _hero(self, detail: CharacterDetail) -> ft.Control:
        heading: list[ft.Control] = [
            ft.Text(detail.name, size=34, weight=ft.FontWeight.BOLD, color=t.TEXT),
        ]
        subtitle = detail.subtitle or detail.faction
        if subtitle:
            heading.append(ft.Text(subtitle, size=20, weight=ft.FontWeight.BOLD, color=t.ACCENT))

        pills = ft.Container(
            width=440,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            t.info_pill("属性", detail.element),
                            t.info_pill("职业", detail.specialty),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            t.info_pill("出生日期", detail.birthday),
                            t.info_pill("身高", detail.height),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=8,
            ),
        )

        left = ft.Column(heading + [pills], spacing=12, expand=True)

        # 未上线角色没有立绘，这时给个占位，别塞空 src（会渲染成红色报错块）
        portrait_layers: list[ft.Control] = []
        if detail.portrait:
            portrait_layers.append(
                ft.Image(src=detail.portrait, fit=ft.BoxFit.CONTAIN, expand=True)
            )
        else:
            portrait_layers.append(
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                        size=40,
                        color=t.TEXT_DIM,
                    ),
                )
            )

        if detail.rarity:
            portrait_layers.append(
                ft.Container(
                    right=0,
                    bottom=0,
                    content=t.badge(
                        detail.rarity,
                        t.RARITY_COLORS.get(detail.rarity, t.ACCENT),
                        size=18,
                    ),
                )
            )

        portrait = ft.Container(
            width=280,
            height=280,
            content=ft.Stack(portrait_layers, expand=True),
        )

        return ft.Container(
            bgcolor=t.CARD,
            border_radius=8,
            padding=20,
            content=ft.Row(
                [left, portrait],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _skills(self, detail: CharacterDetail) -> list[ft.Control]:
        blocks: list[ft.Control] = []
        for group in detail.skills:
            blocks.append(
                ft.Text(
                    group.name,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=t.ACCENT,
                )
            )
            for skill in group.skills:
                blocks.append(
                    ft.Container(
                        bgcolor=t.CARD_HI,
                        border_radius=6,
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Text(skill.name, size=13, weight=ft.FontWeight.BOLD, color=t.TEXT),
                                ft.Text(
                                    skill.desc,
                                    size=12,
                                    color=t.TEXT_DIM,
                                    selectable=True,
                                ),
                            ],
                            spacing=5,
                        ),
                    )
                )
        return blocks
