# 本地运行与行情数据源配置

本目录提供可启动的 Vue 工作台和 FastAPI 后端，包含基金、股票、持仓管理、市场热点和智能体中心。指数、基金、股票与新闻数据固定于 **2026-10-16 15:00（北京时间）**，用于稳定预览页面；持仓及智能体配置保存在浏览器本地。对话只生成示例回复；附件和知识文件选择只记录文件名，不会上传或读取文件内容，也不会发送模型请求。基金自选保存在本机 SQLite。

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

## 启动前端

再开一个终端窗口：

```bash
cd demo/frontend
npm install
npm run dev
```

按终端提示打开本地页面。Vite 会把 `/api` 请求转发给本机的 FastAPI 服务。

## 运行测试

后端：

```bash
cd demo/backend
py -m pip install -r requirements-dev.txt
py -m pytest
```

非 Windows 环境将 `py` 替换为 `python3`。测试覆盖健康检查、行情样例、自选新增/删除、重复项、无效输入和基金/股票上游 API 配置及请求。
