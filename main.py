"""绝区零 · 代理人图鉴。

列表每次启动实时抓，详情点了才抓（同一 session 内会缓存）。

运行:
    uv run flet run main.py          # 桌面窗口
    uv run flet run --web main.py    # 浏览器
"""

from __future__ import annotations

import flet as ft

from detail import CharacterDetail, fetch_detail
from fetch import Character, fetch_characters
from ui import theme as t
from ui.agent_detail import AgentDetailView
from ui.agent_list import AgentListView

TAB_LIST = 0
TAB_DETAIL = 1


def main(page: ft.Page) -> None:
    page.title = "绝区零 · 代理人图鉴"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = t.BG
    page.padding = ft.Padding.symmetric(horizontal=18, vertical=14)

    detail_view = AgentDetailView(page)
    detail_view.show_empty()

    # 同一 session 内点过的角色不重复请求
    detail_cache: dict[int, CharacterDetail] = {}
    current: dict[str, Character | None] = {"character": None}

    screen = ft.Container(expand=True)

    def show_tab(index: int) -> None:
        screen.content = list_view.root if index == TAB_LIST else detail_view.root
        nav.selected_index = index

    def on_select(character: Character) -> None:
        """列表点卡片：切到详情页并加载。"""
        current["character"] = character
        show_tab(TAB_DETAIL)

        cached = detail_cache.get(character.content_id)
        if cached is not None:
            detail_view.show_detail(cached)
            page.update()
            return

        detail_view.show_loading(character.name)
        page.update()
        page.run_thread(load_detail, character)

    list_view = AgentListView(page, on_select=on_select)

    def load_detail(character: Character) -> None:
        try:
            detail = fetch_detail(character.content_id)
        except Exception as exc:  # 网络 / 接口变更都走这里
            detail_view.show_error(character.name, str(exc))
            page.update()
            return

        detail_cache[character.content_id] = detail
        # 期间用户可能已经点了别的角色，只更新当前那个
        if current["character"] is character:
            detail_view.show_detail(detail)
        page.update()

    def on_nav(e: ft.Event) -> None:
        show_tab(e.control.selected_index)
        page.update()

    def load_agents() -> None:
        try:
            characters = fetch_characters()
        except Exception as exc:
            list_view.show_error(str(exc))
            page.update()
            return
        list_view.set_characters(characters)
        page.update()

    def refresh(e: ft.Event) -> None:
        detail_cache.clear()
        current["character"] = None
        detail_view.show_empty()
        list_view.show_loading()
        show_tab(TAB_LIST)
        page.update()
        page.run_thread(load_agents)

    page.appbar = ft.AppBar(
        title=ft.Text("绳网情报站 · 代理人图鉴", size=16, weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=t.CARD,
        actions=[
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip="重新抓取列表",
                on_click=refresh,
            ),
        ],
    )

    nav = ft.NavigationBar(
        selected_index=TAB_LIST,
        on_change=on_nav,
        bgcolor=t.CARD,
        indicator_color=t.ACCENT,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.GRID_VIEW, label="代理人"),
            ft.NavigationBarDestination(icon=ft.Icons.BADGE, label="详情"),
        ],
    )
    page.navigation_bar = nav

    show_tab(TAB_LIST)
    list_view.show_loading()
    page.add(screen)

    # 启动就实时抓列表
    page.run_thread(load_agents)


if __name__ == "__main__":
    ft.run(main)
