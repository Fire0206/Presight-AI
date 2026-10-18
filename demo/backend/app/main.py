"""FastAPI endpoints for a frozen local market snapshot and local examples.

Market snapshot values are static display data. Fund and stock providers can
optionally be configured by the local operator through environment variables.
"""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as PathParam, status
from pydantic import BaseModel, ConfigDict, Field

from .providers import fetch_market_data

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "demo.sqlite3"

DEMO_SNAPSHOT_AT = "2026-10-16T15:00:00+08:00"

DEMO_OVERVIEW = {
    "data_mode": "frozen-demo-snapshot",
    "snapshot_at": DEMO_SNAPSHOT_AT,
    "snapshot_label": "2026-10-16 收盘快照",
    "notice": "页面展示的是固定于 2026-10-16 15:00（北京时间）的虚构快照，仅用于界面预览，不代表真实行情，也不会自动更新。",
    "indices": [
        {"name": "上证指数", "value": 3726.28, "change_percent": 0.24},
        {"name": "沪深 300", "value": 4216.85, "change_percent": 0.31},
        {"name": "创业板指", "value": 2782.46, "change_percent": -0.18},
        {"name": "科创 50", "value": 1361.72, "change_percent": 0.52},
    ],
    "funds": [
        {
            "code": "DEMO01",
            "name": "示例基金 · 均衡组合",
            "category": "混合型",
            "estimate_percent": 0.68,
            "nav_label": "示例净值 1.236",
            "series": [22, 25, 24, 31, 28, 36, 34, 42, 46, 43, 52, 58],
        },
        {
            "code": "DEMO02",
            "name": "示例基金 · 宽基指数",
            "category": "指数型",
            "estimate_percent": -0.27,
            "nav_label": "示例净值 0.984",
            "series": [52, 47, 50, 44, 48, 39, 41, 36, 40, 34, 32, 29],
        },
        {
            "code": "DEMO03",
            "name": "示例基金 · 科技主题",
            "category": "混合型",
            "estimate_percent": 1.12,
            "nav_label": "示例净值 1.508",
            "series": [18, 21, 19, 29, 26, 32, 37, 33, 43, 47, 45, 61],
        },
    ],
    "stocks": [
        {
            "code": "DEMO-SH-601398",
            "name": "示例银行",
            "market": "沪市主板",
            "sector": "银行",
            "price": 6.18,
            "change_percent": 0.49,
            "open": 6.15,
            "high": 6.22,
            "low": 6.12,
            "turnover": "示例成交额 18.6 亿",
            "series": [28, 31, 29, 34, 33, 38, 36, 42, 40, 45],
        },
        {
            "code": "DEMO-SZ-000858",
            "name": "示例消费",
            "market": "深市主板",
            "sector": "食品饮料",
            "price": 128.40,
            "change_percent": -1.26,
            "open": 130.10,
            "high": 130.80,
            "low": 127.60,
            "turnover": "示例成交额 32.4 亿",
            "series": [55, 53, 57, 48, 50, 44, 46, 38, 41, 35],
        },
        {
            "code": "DEMO-SZ-300750",
            "name": "示例新能源",
            "market": "创业板",
            "sector": "电池",
            "price": 246.80,
            "change_percent": 2.14,
            "open": 241.20,
            "high": 248.60,
            "low": 239.50,
            "turnover": "示例成交额 56.1 亿",
            "series": [18, 21, 20, 27, 24, 34, 32, 42, 47, 58],
        },
    ],
    "sectors": [
        {"name": "人工智能", "change_percent": 1.82, "related_funds": 3},
        {"name": "高端制造", "change_percent": 0.74, "related_funds": 2},
        {"name": "消费服务", "change_percent": -0.36, "related_funds": 1},
    ],
    "headlines": [
        {
            "title": "示例资讯：政策动向带动相关行业关注度上升",
            "category": "政策观察",
            "summary": "这是用于本地演示的虚构新闻摘要，不对应真实事件。",
            "source": "演示资讯",
            "published_at": "2026-10-16T13:45:00+08:00",
        },
        {
            "title": "示例资讯：市场成交结构出现阶段性变化",
            "category": "市场观察",
            "summary": "正式产品会结合新闻和行情展示相关信息；此处仅用于界面预览。",
            "source": "演示资讯",
            "published_at": "2026-10-16T10:30:00+08:00",
        },
    ],
}


class WatchlistCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=1, max_length=60)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(db_path)
        app.state.db_path = db_path
        yield

    app = FastAPI(
        title="知几 Presight 本地示例 API",
        description="提供固定行情快照、本地自选列表示例，以及可自行配置的基金和股票数据源接口。",
        version="2.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "demo"}

    @app.get("/api/demo/overview")
    def get_overview() -> dict:
        return DEMO_OVERVIEW

    @app.get("/api/market/funds")
    async def get_fund_market_data() -> object:
        return await fetch_market_data("fund")

    @app.get("/api/market/stocks")
    async def get_stock_market_data() -> object:
        return await fetch_market_data("stock")

    @app.get("/api/demo/watchlist")
    def get_watchlist() -> list[dict]:
        with connect(app.state.db_path) as connection:
            rows = connection.execute(
                "SELECT id, code, name, created_at FROM demo_watchlist ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    @app.post("/api/demo/watchlist", status_code=status.HTTP_201_CREATED)
    def add_to_watchlist(item: WatchlistCreate) -> dict:
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with connect(app.state.db_path) as connection:
                cursor = connection.execute(
                    "INSERT INTO demo_watchlist (code, name, created_at) VALUES (?, ?, ?)",
                    (item.code.upper(), item.name, created_at),
                )
                row = connection.execute(
                    "SELECT id, code, name, created_at FROM demo_watchlist WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="这个示例代码已经在自选里了") from exc
        return dict(row)

    @app.delete("/api/demo/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remove_from_watchlist(
        item_id: Annotated[int, PathParam(ge=1)],
    ) -> None:
        with connect(app.state.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM demo_watchlist WHERE id = ?",
                (item_id,),
            )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="没有找到这条示例自选")

    return app


app = create_app()
