# 抖音服装测款选品分析 Agent

一个本地可运行的选品决策 Agent（Flask + LangChain + OpenAI 兼容接口），提供决策与反馈 API，并附带简易操作界面。

## 功能概览
- 唯一决策输出（One Shot）
- 不拍清单（defer/avoid）
- 失败预判与行动指令
- 冷启动权威建立期
- 简易网页操作台

## 目录结构
```
.
├─ app.py
├─ .env
├─ requirements.txt
├─ templates
│  └─ index.html
└─ agent
   ├─ api
   │  ├─ __init__.py
   │  ├─ decision.py
   │  ├─ feedback.py
   │  └─ pages.py
   ├─ config.py
   ├─ decision_engine.py
   ├─ llm_agent.py
   ├─ memory_store.py
   ├─ models.py
   ├─ state.py
   └─ tools
      ├─ __init__.py
      └─ decision_tools.py
```

## 环境与依赖
建议使用 conda 环境：
```
conda create -n agent python=3.10
conda activate agent
pip install -r requirements.txt
```

## 配置
在 `.env` 中配置模型与鉴权（OpenAI 兼容）：
```
APP_VERSION=0.260208.07
BASE_URL=__FILL__
MODEL=__FILL__
OPENAI_API_KEY=__FILL__
```

## 路由配置
路由路径配置放在 `agent/api/.routes`：\n```\nINDEX_ROUTE=/\nDECISION_FLASK_API=/v1/decision\nFEEDBACK_FLASK_API=/v1/feedback\n```\n\n## 运行
```
python app.py
```
启动后访问：
- 本机：`http://127.0.0.1:8000/`

## API
### 生成决策
`POST /v1/decision`

请求示例：
```json
{
  "user_id": "u1",
  "category": "top",
  "price_band": "79-129",
  "account_stage": "explore",
  "daily_slots": 2,
  "in_stock": true
}
```

### 提交反馈
`POST /v1/feedback`

请求示例：
```json
{
  "user_id": "u1",
  "decision_id": "<decision_id>",
  "outcome": "no_volume"
}
```

## 备注
- 当前版本使用**内存存储**（`agent/memory_store.py`），服务重启后状态会丢失。
- 如果需要持久化（SQLite 等），请告知我可恢复数据库版本。

## 更新日志
- 2026-02-08 21:30: 初始化工程结构，支持 Flask + LangChain + 简易网页操作台。
- 2026-02-08 21:45: API 拆分到 `agent/api` 目录，路由路径改为从环境变量读取。
- 2026-02-08 22:05: 导航页/选品页/AI问答页拆分为多页面，新增 `/decision` 与 `/chat`。
- 2026-02-08 23:10: AI 对话页面调整为全屏布局，聊天区支持滚动查看历史。
- 2026-02-08 23:20: 导航页更新为双按钮入口，选品与对话页增加顶部导航区。
