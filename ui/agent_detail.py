"""代理人详情页：立绘头图 + 分节内容，照着官网那套版式。"""

from __future__ import annotations

import flet as ft

from detail import CharacterDetail, Media, SkillGroup

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
            intro: list[ft.Control] = []
            if detail.tags:
                intro.append(ft.Row([t.chip(x) for x in detail.tags], wrap=True, spacing=8))
            if detail.intro:
                intro.append(t.body_text(detail.intro))
            sections.append(t.section("角色介绍", *intro))

        if detail.cv:
            sections.append(
                t.section(
                    "角色CV",
                    *[
                        ft.Row(
                            [
                                ft.Text(label, size=13, color=t.TEXT_DIM, width=60),
                                ft.Text(
                                    detail.cv[label], size=13, color=t.TEXT, selectable=True
                                ),
                            ],
                            spacing=12,
                        )
                        for label in CV_ORDER
                        if label in detail.cv
                    ],
                )
            )

        if detail.skills:
            sections.append(
                t.section(
                    "技能展示",
                    *[
                        block
                        for group in detail.skills
                        for block in self._skill_group(group)
                    ],
                )
            )

        if detail.cinema or detail.cinema_levels:
            blocks: list[ft.Control] = []
            if detail.cinema:
                blocks.append(self._gallery(detail.cinema, width=300, height=170))
            blocks.extend(self._cinema_levels(detail))
            sections.append(t.section("意象影画", *blocks))

        if detail.showcase:
            sections.append(
                t.section(
                    "角色展示",
                    self._gallery(detail.showcase, width=260, height=150),
                )
            )

        for title, text in (
            ("角色印象", detail.impression),
            ("角色故事", detail.story),
            ("录像店经营留言信息", detail.store_message),
        ):
            if text:
                sections.append(t.section(title, t.body_text(text)))

        if detail.gallery:
            sections.append(
                t.section(
                    "媒体物料",
                    self._gallery(detail.gallery, width=260, height=150),
                )
            )

        if detail.strategies:
            sections.append(
                t.section(
                    "攻略推荐",
                    ft.Row(
                        [self._strategy(s) for s in detail.strategies],
                        wrap=True,
                        spacing=12,
                        run_spacing=12,
                    ),
                )
            )

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

    # ---- 头图 ----

    def _hero(self, detail: CharacterDetail) -> ft.Control:
        heading: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text(
                        detail.name,
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        color=t.TEXT,
                    ),
                    t.icon_badge(detail.faction_icon, size=52),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

        subtitle = detail.subtitle or detail.faction
        if subtitle:
            heading.append(
                ft.Text(subtitle, size=20, weight=ft.FontWeight.BOLD, color=t.ACCENT)
            )
        if detail.romanized:
            heading.append(ft.Text(detail.romanized, size=12, color=t.TEXT_DIM))

        pills = ft.Container(
            width=460,
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
                    content=t.icon_badge(
                        t.RARITY_ICONS.get(detail.rarity),
                        size=44,
                        fallback=t.badge(
                            detail.rarity,
                            t.RARITY_COLORS.get(detail.rarity, t.ACCENT),
                            size=18,
                        ),
                    ),
                )
            )

        portrait = ft.Container(
            width=320,
            height=320,
            content=ft.Stack(portrait_layers, expand=True),
        )

        return ft.Container(
            border_radius=8,
            padding=20,
            # 官网头图是角色主题色铺的，这里用同色系的渐变做背景
            gradient=ft.LinearGradient(
                colors=[t.blend(detail.accent), t.blend(detail.accent, ratio=0.06)],
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
            ),
            content=ft.Row(
                [left, portrait],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ---- 各分节 ----

    def _skill_group(self, group: SkillGroup) -> list[ft.Control]:
        head: list[ft.Control] = []
        if group.icon:
            head.append(
                ft.Image(src=group.icon, width=30, height=30, fit=ft.BoxFit.CONTAIN)
            )
        head.append(
            ft.Text(group.name, size=14, weight=ft.FontWeight.BOLD, color=t.ACCENT)
        )

        blocks: list[ft.Control] = [
            ft.Row(head, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ]

        for skill in group.skills:
            row: list[ft.Control] = []
            if skill.icon:
                # 招式演示是动图，Flutter 的 Image 会直接播
                row.append(
                    ft.Image(
                        src=skill.icon,
                        width=120,
                        height=68,
                        fit=ft.BoxFit.COVER,
                        border_radius=4,
                    )
                )
            row.append(
                ft.Column(
                    [
                        ft.Text(
                            skill.name,
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=t.TEXT,
                        ),
                        ft.Text(
                            skill.desc,
                            size=12,
                            color=t.TEXT_DIM,
                            selectable=True,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                )
            )
            blocks.append(
                ft.Container(
                    bgcolor=t.CARD_HI,
                    border_radius=6,
                    padding=12,
                    content=ft.Row(
                        row,
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                )
            )
        return blocks

    def _gallery(
        self, items: list[Media], *, width: int, height: int
    ) -> ft.Control:
        """图集：固定尺寸的图片 + 页签名。"""
        return ft.Row(
            [
                ft.Column(
                    [
                        ft.Container(
                            width=width,
                            height=height,
                            border_radius=6,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            bgcolor=t.CARD_HI,
                            content=ft.Image(
                                src=item.image,
                                fit=ft.BoxFit.COVER,
                                expand=True,
                            ),
                        ),
                        ft.Text(
                            item.name,
                            size=12,
                            color=t.TEXT_DIM,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            width=width,
                        ),
                    ],
                    spacing=6,
                    tight=True,
                )
                for item in items
                if item.image
            ],
            wrap=True,
            spacing=12,
            run_spacing=12,
        )

    def _cinema_levels(self, detail: CharacterDetail) -> list[ft.Control]:
        blocks: list[ft.Control] = []
        for level in detail.cinema_levels:
            head: list[ft.Control] = [
                ft.Text(level.level, size=12, weight=ft.FontWeight.BOLD, color=t.ACCENT)
            ]
            if level.name:
                head.append(ft.Text(level.name, size=13, color=t.TEXT))
            blocks.append(
                ft.Container(
                    bgcolor=t.CARD_HI,
                    border_radius=6,
                    padding=12,
                    content=ft.Column(
                        [
                            ft.Row(head, spacing=10),
                            *(
                                [t.body_text(level.effect)]
                                if level.effect
                                else []
                            ),
                        ],
                        spacing=6,
                    ),
                )
            )
        return blocks

    def _strategy(self, strategy) -> ft.Control:
        cover: list[ft.Control] = []
        if strategy.cover:
            cover.append(
                ft.Container(
                    width=200,
                    height=100,
                    border_radius=6,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(src=strategy.cover, fit=ft.BoxFit.COVER, expand=True),
                )
            )
        cover.append(
            ft.Text(
                strategy.name,
                size=12,
                color=t.TEXT,
                width=200,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )
        return ft.Column(cover, spacing=6, tight=True)
