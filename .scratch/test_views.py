"""把 62 个角色都灌进两个视图里构造一遍，抓参数写错/边界情况。

Flet 在构造控件时就会校验参数，所以这一步能抓到大部分布局代码的错。
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import detail as D  # noqa: E402
from fetch import Character  # noqa: E402
from ui.agent_detail import AgentDetailView  # noqa: E402
from ui.agent_list import AgentListView  # noqa: E402

views = 0
list_view = AgentListView(None, on_select=lambda c: None)
list_view.set_characters([Character(content_id=1, name="测试")])
views += 1
print("列表页空数据 OK")

detail_view = AgentDetailView(None)

files = sorted(glob.glob(".scratch/details/*.json"), key=lambda f: int(os.path.basename(f)[:-5]))
ok = 0
for f in files:
    parsed = D.parse_detail(json.load(open(f, encoding="utf-8")))
    try:
        detail_view.show_detail(parsed)
        ok += 1
    except Exception as exc:
        print(f"  !! {parsed.name}: {type(exc).__name__}: {exc}")

print(f"详情页构造成功 {ok}/{len(files)}")

# 空状态
detail_view.show_empty()
detail_view.show_loading("测试")
detail_view.show_error("测试", "boom")
print("空/加载/错误态 OK")

# 列表：无图标的角色
list_view.set_characters(
    [
        Character(content_id=2, name="没图标", icon="", rarity=None, element=None),
        Character(content_id=3, name="没简称", short_name="", rarity="S", element="电"),
    ]
)
print("列表页缺字段 OK")
