"""Configurable HTTP adapters for user-selected fund and stock data APIs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException

MarketType = Literal["fund", "stock"]
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class ProviderConfig:
    endpoint: str
    api_key: str
    key_header: str
    auth_scheme: str


def load_provider_config(market: MarketType) -> ProviderConfig:
    prefix = "FUND" if market == "fund" else "STOCK"
    return ProviderConfig(
        endpoint=os.getenv(f"{prefix}_MARKET_API_URL", "").strip(),
        api_key=os.getenv(f"{prefix}_MARKET_API_KEY", "").strip(),
        key_header=os.getenv(f"{prefix}_MARKET_API_KEY_HEADER", "Authorization").strip(),
        auth_scheme=os.getenv(f"{prefix}_MARKET_API_AUTH_SCHEME", "Bearer").strip(),
    )


def create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10.0, follow_redirects=False)


async def fetch_market_data(market: MarketType) -> object:
    config = load_provider_config(market)
    label = "基金" if market == "fund" else "股票"
    if not config.endpoint:
        raise HTTPException(status_code=503, detail=f"尚未配置{label}行情数据源。")

    parsed_endpoint = urlsplit(config.endpoint)
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.netloc:
        raise HTTPException(status_code=503, detail=f"{label}行情数据源地址配置无效。")

    headers: dict[str, str] = {"Accept": "application/json"}
    if config.api_key:
        if not config.key_header:
            raise HTTPException(status_code=503, detail=f"{label}行情数据源认证配置无效。")
        auth_value = f"{config.auth_scheme} {config.api_key}".strip()
        headers[config.key_header] = auth_value

    try:
        async with create_http_client() as client:
            async with client.stream("GET", config.endpoint, headers=headers) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                    raise HTTPException(status_code=502, detail=f"{label}行情数据响应过大。")

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise HTTPException(status_code=502, detail=f"{label}行情数据响应过大。")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"{label}行情数据源返回异常。") from exc
    except (httpx.TimeoutException, httpx.RequestError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"暂时无法读取{label}行情数据。") from exc

    try:
        return json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=502, detail=f"{label}行情数据源未返回有效 JSON。") from exc
