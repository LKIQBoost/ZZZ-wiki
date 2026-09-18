# 绝区零角色图鉴

爬米游社百科（绳网情报站）的代理人数据，并提供一个 Flet 桌面界面。

## 用法

```bash
uv run flet run main.py    # 图形界面（推荐桌面模式）

uv run python fetch.py     # 只抓列表 -> agents.json（62 个代理人）
uv run python detail.py    # 只抓详情 -> details.json
```

## 界面

底部 NavigationBar 两项：**代理人**（卡片网格，可按稀有度/属性/特性/阵营筛选）和 **详情**。
列表每次启动实时抓；详情点了某个角色才抓，同一 session 内点过的会缓存，不重复请求。

> **图片只在桌面模式显示。** `flet run --web` 下角色图会全部空白：Flet 的 web 渲染器用
> XHR 取图，而米游社 OSS 不返回 `Access-Control-Allow-Origin`，被浏览器 CORS 拦掉。
> 桌面模式走原生图片加载，没有这个限制。
>
> 另外首次用 `--web` 时 Flet 会自动往 venv 里装 `flet-web` 等十来个包（不改 `pyproject.toml`）。

## 接口

图鉴页是 Nuxt 单页应用，直接抓 HTML 只能拿到空壳，数据都在 XHR 里：

| 用途 | 接口 |
| --- | --- |
| 角色列表 | `api-takumi-static.mihoyo.com/common/blackboard/zzz_wiki/v1/home/content/list?app_sn=zzz_wiki&channel_id=43` |
| 角色详情 | `act-api-takumi-static.mihoyo.com/hoyowiki/zzz/wapi/entry_page?app_sn=zzz_wiki&entry_page_id=<content_id>&lang=zh-cn` |

URL 里的 `channel/map/2/43`，接口要的是 `channel_id=43`（`2` 是它的父频道）。

### 两个坑

1. **详情接口必须带 `x-rpc-wiki_app: zzz` 头**，否则一律返回 `retcode=404`「信号好像消失了」，看起来像词条不存在。
2. 详情页名字下面那行（`addition_text`）**不总是阵营**——多数角色是阵营，但 `叶瞬光` 是「虚狩·青溟司命」、`仪玄` 是「宗师」。所以 `faction` 统一取列表接口的 `阵营` 标签，详情页那行另存在 `subtitle`。

列表页的属性/特性在接口里是英文枚举（`electric` / `strike`），映射表见 `detail.py` 的 `ELEMENTS`、`SPECIALTIES`。

## 产出

`agents.json`：图鉴列表页能看到的字段。

```json
{
  "content_id": 147, "name": "安东·伊万诺夫", "short_name": "安东",
  "element": "电", "specialty": "强攻", "faction": "白祇重工", "rarity": "A",
  "icon": "https://...", "detail_url": "https://..."
}
```

`details.json`：在列表基础上加了简介、技能、CV、故事等，`skills` 按「普攻 / 闪避 / 支援技 / 特殊技 / 终结技 / 核心技」分组。

## 数据缺口（源头就缺，不是解析问题）

- `菲欧妮·蕾法爱菈`、`赛维里安·洛威尔` 是未上线角色（`corner_mark: "Pre"`），没有稀有度和技能，字段大量为空。
- `佩洛伊斯` 缺生日/身高/角色印象，`洛克茜` 缺 TAG/简介，另有 5 个角色没有「角色故事」。
- CV 面板有「中配」和「中文CV」两种写法，解析时已统一。

## 兜底

`fetch.py` 的列表抓取在接口失败时会回退到 `DynamicFetcher` 渲染 DOM。此时只能拿到名字、图标和 content_id——属性和稀有度在 DOM 里是 base64 图片，取不到。
