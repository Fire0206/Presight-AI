# 本地可运行示例

这里包含一个简化的 Vue 前端和 FastAPI 后端，可以在本机启动、查看前端和 API 的连接，并体验一个写入本地 SQLite 的自选列表。

所有行情、基金和资讯均为虚构示例。这里没有生产环境密钥、用户数据、市场数据接口、股票数据源或 AI 智能体核心代码，也不会连接 `presight.cloud` 的生产 API。不要把这个仅供本机开发的示例直接部署到公网。

## 环境要求

- Node.js 20.19 或更新版本
- Python 3.11 或更新版本

无需配置 `.env` 或 API Key。

## 启动后端

在一个终端窗口执行：

```powershell
cd demo/backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS / Linux：

```bash
cd demo/backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

可在 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看本地 API 文档。第一次运行会在 `demo/backend/data/` 建立本地自选数据库。

## 启动前端

再开一个终端窗口：

```bash
cd demo/frontend
npm install
npm run dev
```

按终端提示打开本地页面。Vite 会把 `/api` 请求转发给本机的 FastAPI 服务。

## 运行后端测试

```bash
cd demo/backend
py -m pip install -r requirements-dev.txt
py -m pytest
```

非 Windows 环境将 `py` 替换为 `python3`。测试覆盖健康检查、示例数据标记、自选新增/删除、重复项和无效输入。
