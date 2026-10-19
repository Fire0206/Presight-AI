"""Small OpenAI-compatible chat adapter for local demos.

It deliberately provides plain text chat only: no tools, agent orchestration,
retrieval, or provider reasoning fields are exposed by this public example.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException

MAX_RESPONSE_BYTES = 1_000_000
MAX_COMPLETION_TOKENS = 2_048
MAX_ANSWER_CHARACTERS = 32_000


@dataclass(frozen=True)
class ModelConfig:
    enabled: bool
    endpoint: str
    api_key: str
    model: str
    max_tokens: int
    timeout_seconds: float


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(value, maximum))


def load_model_config() -> ModelConfig:
    return ModelConfig(
        enabled=os.getenv("MODEL_CHAT_ENABLED", "false").strip().lower() in {"1", "true", "yes"},
        endpoint=os.getenv("MODEL_API_URL", "").strip(),
        api_key=os.getenv("MODEL_API_KEY", "").strip(),
        model=os.getenv("MODEL_NAME", "").strip(),
        max_tokens=_bounded_int("MODEL_MAX_TOKENS", 512, 64, MAX_COMPLETION_TOKENS),
        timeout_seconds=float(_bounded_int("MODEL_TIMEOUT_SECONDS", 30, 3, 60)),
    )


def model_is_configured() -> bool:
    config = load_model_config()
    if not (config.enabled and config.endpoint and config.api_key and config.model):
        return False
    try:
        parsed_endpoint = urlsplit(config.endpoint)
    except ValueError:
        return False
    if not parsed_endpoint.netloc or parsed_endpoint.username or parsed_endpoint.password:
        return False
    return parsed_endpoint.scheme == "https" or (
        parsed_endpoint.scheme == "http" and parsed_endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
    )


def create_http_client(timeout_seconds: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False)


async def complete_chat(messages: list[dict[str, str]]) -> str:
    config = load_model_config()
    if not (config.enabled and config.endpoint and config.api_key and config.model):
        raise HTTPException(
            status_code=503,
            detail="模型接口尚未配置。请在后端 .env 中填写接口地址、密钥和模型名并启用聊天。",
        )

    if not model_is_configured():
        raise HTTPException(status_code=503, detail="模型接口地址配置无效。")

    payload = {
        "model": config.model,
        "messages": messages,
        "max_tokens": config.max_tokens,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        async with create_http_client(config.timeout_seconds) as client:
            async with client.stream("POST", config.endpoint, json=payload, headers=headers) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                    raise HTTPException(status_code=502, detail="模型响应过大。")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise HTTPException(status_code=502, detail="模型响应过大。")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="模型服务暂时不可用，请检查接口配置或稍后重试。") from exc
    except (httpx.TimeoutException, httpx.RequestError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="暂时无法连接模型服务，请检查接口配置或稍后重试。") from exc

    try:
        result = json.loads(body)
        answer = result["choices"][0]["message"].get("content")
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="模型服务没有返回兼容的文本回答。") from exc

    if not isinstance(answer, str) or not answer.strip():
        # In particular, reasoning_content and other private fields are not a fallback.
        raise HTTPException(status_code=502, detail="模型服务没有返回可展示的文本回答。")
    answer = answer.strip()
    if len(answer) > MAX_ANSWER_CHARACTERS:
        answer = answer[:MAX_ANSWER_CHARACTERS].rstrip() + "\n\n（回答过长，已按本地演示上限截断。）"
    return answer
