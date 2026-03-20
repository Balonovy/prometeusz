from __future__ import annotations

import argparse
import importlib
import inspect
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from pydantic import BaseModel


def resolve_app(target: str):
    module_name, app_name = target.split(':', 1)
    module = importlib.import_module(module_name)
    return getattr(module, app_name)


def invoke_handler(handler, body):
    signature = inspect.signature(handler)
    kwargs = {}
    for name, param in signature.parameters.items():
        annotation = param.annotation
        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            kwargs[name] = annotation(**body)
        elif name in body:
            kwargs[name] = body[name]
        elif param.default is not inspect._empty:
            kwargs[name] = param.default
    result = handler(**kwargs)
    if inspect.iscoroutine(result):
        import asyncio
        return asyncio.run(result)
    return result


def match_route(route_path: str, request_path: str):
    route_parts = [part for part in route_path.strip('/').split('/') if part]
    request_parts = [part for part in request_path.strip('/').split('/') if part]
    if len(route_parts) != len(request_parts):
        return False, {}
    params = {}
    for route_part, request_part in zip(route_parts, request_parts):
        if route_part.startswith('{') and route_part.endswith('}'):
            params[route_part[1:-1]] = request_part
        elif route_part != request_part:
            return False, {}
    return True, params


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def _handle(self, method: str):
            parsed = urlparse(self.path)
            length = int(self.headers.get('Content-Length', '0') or 0)
            raw = self.rfile.read(length) if length else b''
            body = json.loads(raw.decode() or '{}') if raw else {}
            for route in app.routes:
                matched, params = match_route(route.path, parsed.path)
                if route.method == method and matched:
                    payload = invoke_handler(route.handler, {**body, **params})
                    encoded = json.dumps(payload).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                    return
            self.send_response(404)
            self.end_headers()
        def do_GET(self):
            self._handle('GET')
        def do_POST(self):
            self._handle('POST')
        def log_message(self, fmt, *args):
            return
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('app')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    app = resolve_app(args.app)
    
    if getattr(app, 'lifespan', None) is not None:
        import asyncio
        lifespan_cm = app.lifespan(app)
        asyncio.run(lifespan_cm.__aenter__())
    else:
        lifespan_cm = None
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if lifespan_cm is not None:
            import asyncio
            asyncio.run(lifespan_cm.__aexit__(None, None, None))


if __name__ == '__main__':
    main()
