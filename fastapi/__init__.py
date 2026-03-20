from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass
class Route:
    method: str
    path: str
    handler: Callable[..., Any]


class APIRouter:
    def __init__(self, prefix: str = '', tags: list[str] | None = None) -> None:
        self.prefix = prefix
        self.tags = tags or []
        self.routes: list[Route] = []
        self.websocket_routes: dict[str, Callable[..., Any]] = {}

    def get(self, path: str):
        return self._register('GET', path)

    def post(self, path: str):
        return self._register('POST', path)

    def websocket(self, path: str):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.websocket_routes[self.prefix + path] = fn
            return fn
        return decorator

    def _register(self, method: str, path: str):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(Route(method, self.prefix + path, fn))
            return fn
        return decorator


class FastAPI(APIRouter):
    def __init__(self, title: str = '', version: str = '', lifespan: Any = None) -> None:
        super().__init__(prefix='')
        self.title = title
        self.version = version
        self.lifespan = lifespan
        self._routers: list[APIRouter] = []

    def include_router(self, router: APIRouter) -> None:
        self.routes.extend(router.routes)
        self.websocket_routes.update(router.websocket_routes)
        self._routers.append(router)

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:
        return None


class WebSocketDisconnect(Exception):
    pass


class WebSocket:
    def __init__(self) -> None:
        self.messages: list[Any] = []
    async def accept(self) -> None:
        return None
    async def send_json(self, payload: Any) -> None:
        self.messages.append(payload)
    async def close(self) -> None:
        return None


def _run_async(callable_obj: Any) -> Any:
    if inspect.iscoroutine(callable_obj):
        return asyncio.run(callable_obj)
    return callable_obj
