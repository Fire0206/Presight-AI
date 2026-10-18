# 本地运行与行情数据源配置

本目录提供可启动的 Vue 工作台和 FastAPI 后端。工作台内置指数、基金、板块和资讯数据，基金自选保存在本机 SQLite；后端另提供基金与股票行情 API 代理，便于连接自己选择的数据服务。

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

首次运行会在 `demo/backend/data/` 建立本地自选数据库。可在 [本地 API 文档](http://127.0.0.1:8000/docs) 查看全部接口。

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

后端提供 `GET /api/market/funds` 和 `GET /api/market/stocks`，会在服务端请求配置的地址，并将 JSON 响应返回。接口支持常见的 Header 密钥认证，单次响应上限为 2 MB、请求超时为 10 秒；密钥不会返回给浏览器。数据源未配置时返回 `503`，上游异常或响应格式不正确时返回可读错误。

不同服务商的字段结构并不相同；连接成功后，可根据所选接口的数据结构，将字段映射到前端需要的行情格式。仓库页面默认使用内置示例行情，便于在尚未配置数据源时浏览和开发。

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
