"""FastAPI endpoints for market research and local portfolio examples.

The overview defaults to sample data. Fund and stock providers are configurable
through environment variables and remain server-side.
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

DEMO_OVERVIEW = {
    "data_mode": "fictional-demo",
    "notice": "页面内数字为虚构示例，仅用于演示界面和 API，不代表实时行情。",
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
        },
        {
            "title": "示例资讯：市场成交结构出现阶段性变化",
            "category": "市场观察",
            "summary": "正式产品会结合新闻和行情展示相关信息；此处仅用于界面预览。",
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
        description="只提供虚构演示数据和本地自选列表，不连接线上服务。",
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
