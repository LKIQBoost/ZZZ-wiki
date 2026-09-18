"""以 web 模式跑 app 但不开浏览器，方便截图验收。"""

import os
import sys

import flet.app as fapp

fapp.open_in_browser = lambda url: print(f"SERVING: {url}", flush=True)

import flet as ft  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from main import main  # noqa: E402

ft.run(main, view=ft.AppView.WEB_BROWSER, port=8551, assets_dir=os.path.join(ROOT, "assets"))
