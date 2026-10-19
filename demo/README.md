# 本地运行与行情数据源配置

本目录提供可启动的 Vue 工作台和 FastAPI 后端，包含基金、股票、持仓管理、市场热点和智能体中心。指数、基金、股票与新闻数据固定于 **2026-10-16 15:00（北京时间）**，用于稳定预览页面；持仓及智能体配置保存在浏览器本地。默认对话使用示例回复；也可以按下文接入自己提供的 OpenAI 兼容聊天接口。对话附件和知识文件选择只记录文件名，不会上传或读取文件内容；所选 Skills 和知识资料是界面演示配置，不会被加入模型请求。基金自选保存在本机 SQLite。

## 环境要求

- Node.js 20.19 或更新版本
- Python 3.11 或更新版本

## 启动后端

在一个终端窗口执行：

```powershell
cd demo/backend
py -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

macOS / Linux：

```bash
cd demo/backend
python3 -m venv .venv
cp .env.example .env
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

首次运行会在 `demo/backend/data/` 建立本地自选数据库。可在 [本地 API 文档](http://127.0.0.1:8000/docs) 查看全部接口。固定快照通过 `/api/demo/overview` 提供，重复读取会返回相同数据。

## 配置基金和股票行情接口

编辑 `demo/backend/.env`，按服务商提供的信息填写：

| 配置项 | 用途 |
| --- | --- |
| `FUND_MARKET_API_URL` | 基金行情 JSON 接口完整地址 |
| `FUND_MARKET_API_KEY` | 基金服务商密钥 |
| `FUND_MARKET_API_KEY_HEADER` | 密钥请求头名称，默认 `Authorization` |
| `FUND_MARKET_API_AUTH_SCHEME` | 认证前缀，默认 `Bearer`；自定义密钥头可留空 |
| `STOCK_MARKET_API_URL` | 股票行情 JSON 接口完整地址 |
| `STOCK_MARKET_API_KEY` | 股票服务商密钥 |
| `STOCK_MARKET_API_KEY_HEADER` | 密钥请求头名称，默认 `Authorization` |
| `STOCK_MARKET_API_AUTH_SCHEME` | 认证前缀，默认 `Bearer`；自定义密钥头可留空 |

后端提供 `GET /api/market/funds` 和 `GET /api/market/stocks` 两个数据源接入位置，会在服务端请求你填写的地址，并将 JSON 响应返回。接口支持常见的 Header 密钥认证，单次响应上限为 2 MB、请求超时为 10 秒；密钥不会返回给浏览器。数据源未配置时返回 `503`，上游异常或响应格式不正确时返回可读错误。

不同服务商的字段结构并不相同；连接成功后，可根据所选接口的数据结构，将字段映射到前端需要的行情格式。即使没有配置外部数据源，页面也会展示固定快照，方便浏览和开发。

`.env` 已加入 Git 忽略规则。请勿提交真实密钥，也不要在没有鉴权、访问控制和限流的情况下将本地示例服务直接暴露到公网。

## 配置一个自己的聊天模型（可选）

后端提供一个普通文本聊天适配器，兼容采用 OpenAI Chat Completions 请求格式的服务。它只负责把最近的对话文字发送给你在本机配置的模型，并读取 `choices[0].message.content`；不包含 Presight 的 Agent 编排、Skills 调用、RAG、长期记忆或多模态文件解析。模型的思考字段不会作为回答返回。

在后端 `.env` 中填写以下配置：

```dotenv
MODEL_CHAT_ENABLED=true
MODEL_API_URL=https://你的服务商/v1/chat/completions
MODEL_API_KEY=替换为你自己的密钥
MODEL_NAME=替换为服务商的模型标识
MODEL_MAX_TOKENS=512
MODEL_TIMEOUT_SECONDS=30
```

重启后端后，智能体中心会显示已配置状态并把对话文字发送到这个接口。模型名和密钥仅保存在后端环境变量中；浏览器不会收到密钥。默认配置 `MODEL_CHAT_ENABLED=false`，因此第一次启动无需模型账号或密钥。请求最多包含 12 条历史消息，单条最多 8,000 个字符，总输入最多 16,000 个字符；上游响应 JSON 限制为 1 MB，用户可见回答限制为 32,000 个字符，生成上限可配置为 64–2,048 tokens，超时可配置为 3–60 秒。

该接口没有用户登录、计费、全局限流或公网滥用防护；这里只适合本地开发验证。按上面的命令将后端绑定到 `127.0.0.1`，不要用 `0.0.0.0` 或把端口转发到公网。若要部署为多人服务，先补充鉴权、配额、速率限制、审计和密钥管理。

## 启动前端

再开一个终端窗口：

```bash
cd demo/frontend
npm install
npm run dev
```

按终端提示打开本地页面。Vite 会把 `/api` 请求转发给本机的 FastAPI 服务。

如果本机的 8000 端口已被占用，可以让后端改用其他端口（例如 8001），并在启动 Vite 前设置代理地址：PowerShell 使用 `$env:PRESIGHT_DEMO_API_TARGET='http://127.0.0.1:8001'`，macOS/Linux 使用 `export PRESIGHT_DEMO_API_TARGET=http://127.0.0.1:8001`。

## 运行测试

后端：

```bash
cd demo/backend
py -m pip install -r requirements-dev.txt
py -m pytest
```

非 Windows 环境将 `py` 替换为 `python3`。测试覆盖健康检查、行情样例、自选新增/删除、重复项、无效输入和基金/股票上游 API 配置及请求。

根目录的 `npm test` 还会运行行情格式化、持仓快照计算和 Markdown 回答解析测试。持仓计算器只演示已确认快照与有效盘中估值的数学口径，不处理基金节假日、QDII 确认时点或待确认交易；实际接入时需要根据自己的服务端业务规则补齐。
