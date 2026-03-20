from __future__ import annotations

import asyncio
import inspect
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class Response:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class TestClient:
    __test__ = False

    def __init__(self, app: Any) -> None:
        self.app = app
        self._lifespan_cm = None

    def __enter__(self):
        if self.app.lifespan is not None:
            self._lifespan_cm = self.app.lifespan(self.app)
            asyncio.run(self._lifespan_cm.__aenter__())
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._lifespan_cm is not None:
            asyncio.run(self._lifespan_cm.__aexit__(exc_type, exc, tb))
        return False

    def get(self, path: str, json: dict[str, Any] | None = None) -> Response:
        return self.request('GET', path, json=json)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Response:
        return self.request('POST', path, json=json)

    def request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Response:
        for route in self.app.routes:
            matched, path_params = self._match_route(route.path, path)
            if route.method == method and matched:
                try:
                    payload = self._invoke(route.handler, {**(json or {}), **path_params})
                    return Response(200, payload)
                except HTTPException as exc:
                    return Response(exc.status_code, {'detail': exc.detail})
        return Response(404, {'detail': 'Not found'})

    def _match_route(self, route_path: str, request_path: str) -> tuple[bool, dict[str, str]]:
        route_parts = [part for part in route_path.strip('/').split('/') if part]
        request_parts = [part for part in request_path.strip('/').split('/') if part]
        if len(route_parts) != len(request_parts):
            return False, {}
        params: dict[str, str] = {}
        for route_part, request_part in zip(route_parts, request_parts):
            if route_part.startswith('{') and route_part.endswith('}'):
                params[route_part[1:-1]] = request_part
            elif route_part != request_part:
                return False, {}
        return True, params

    def _invoke(self, handler: Any, payload: dict[str, Any]) -> Any:
        signature = inspect.signature(handler)
        kwargs = {}
        for name, param in signature.parameters.items():
            annotation = param.annotation
            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                kwargs[name] = annotation(**payload)
            elif name in payload:
                kwargs[name] = payload[name]
            elif param.default is not inspect._empty:
                kwargs[name] = param.default
        result = handler(**kwargs)
        if inspect.iscoroutine(result):
            return asyncio.run(result)
        return result
