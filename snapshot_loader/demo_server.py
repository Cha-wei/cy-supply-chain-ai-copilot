"""Loopback-only SIMULATED Portfolio transport. No hosted-provider composition."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from threading import BoundedSemaphore
from urllib.parse import unquote, urlsplit

from .demo_session import DemoError, DemoSession

MAX_BODY = 32768
MAX_CONNECTIONS = 8


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def invalid_constant(_):
    raise ValueError("non-JSON number")


def build_assets(root):
    root = Path(root).resolve(strict=True)
    if not (root / "index.html").is_file():
        raise ValueError("React build missing: run npm run build separately")
    assets = {}
    for item in root.rglob("*"):
        resolved = item.resolve(strict=True)
        if item.is_symlink() or not resolved.is_relative_to(root):
            raise ValueError("build root contains unsafe link")
        if item.is_file():
            route = "/" + item.relative_to(root).as_posix()
            # Only Vite's build output, not adjacent repository/configuration files.
            if route == "/index.html" or route.startswith("/assets/"):
                assets[route] = (item.read_bytes(), mimetypes.guess_type(item.name)[0] or "application/octet-stream")
    return assets


class DemoServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    request_queue_size = MAX_CONNECTIONS

    def __init__(self, address, build_root, *, session=None):
        if address[0] != "127.0.0.1":
            raise ValueError("Demo server must bind 127.0.0.1")
        self.assets = build_assets(build_root)  # fail before binding; never spawn frontend tools
        self.session = session if session is not None else DemoSession()
        self.slots = BoundedSemaphore(MAX_CONNECTIONS)
        try:
            super().__init__(address, Handler)
        except Exception:
            self.session.close()
            raise
        self.allowed_host = f"127.0.0.1:{self.server_port}"
        self.origin = "http://" + self.allowed_host

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        pass  # never log request, traceback or provider material

    def server_close(self):
        super().server_close()  # join bounded request threads before deleting session input
        self.session.close()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # one bounded request per connection, no pipelining
    server_version = "SIMULATED-Demo"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(3)

    def log_message(self, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        self._json(code, {"error": "invalid_http_request"})

    def _send(self, code, payload, content_type):
        self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _json(self, code, value):
        self._send(code, json.dumps(value, ensure_ascii=True, allow_nan=False).encode(), "application/json; charset=utf-8")

    def _validate(self, mutation=False):
        if self.headers.get_all("Host") != [self.server.allowed_host]:
            raise DemoError("host_denied", 403)
        origins = self.headers.get_all("Origin")
        if (mutation or origins is not None) and origins != [self.server.origin]:
            raise DemoError("origin_denied", 403)
        if self.headers.get("Transfer-Encoding") is not None or self.headers.get("Expect") is not None:
            raise DemoError("invalid_framing", 400)
        parsed = urlsplit(self.path)
        decoded = unquote(parsed.path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or "\\" in decoded or "%" in decoded:
            raise DemoError("path_denied", 400)
        if any(part in {".", ".."} for part in decoded.split("/")) or any(ord(c) < 32 for c in decoded):
            raise DemoError("path_denied", 400)
        return decoded

    def do_GET(self):
        try:
            route = self._validate()
            if self.headers.get_all("Content-Length") not in (None, ["0"]):
                raise DemoError("invalid_framing", 400)
            if route == "/demo/state":
                self._json(200, self.server.session.snapshot())
                return
            if route in {"/", "/procurement/SIM-M2"}:
                route = "/index.html"
            if route not in self.server.assets:
                raise DemoError("not_found", 404)
            payload, mime = self.server.assets[route]
            self._send(200, payload, mime)
        except DemoError as error:
            self._json(error.status, {"error": error.code})
        except Exception:
            self._json(503, {"error": "unavailable"})

    def do_POST(self):
        try:
            if self._validate(mutation=True) != "/demo/intent":
                raise DemoError("not_found", 404)
            if self.headers.get_all("Content-Type") != ["application/json"]:
                raise DemoError("invalid_content_type", 400)
            lengths = self.headers.get_all("Content-Length") or []
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit() or len(lengths[0]) > 8:
                raise DemoError("invalid_framing", 400)
            length = int(lengths[0])
            if length < 1 or length > MAX_BODY:
                raise DemoError("body_limit", 413)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise DemoError("invalid_framing", 400)
            try:
                request = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object, parse_constant=invalid_constant)
            except (ValueError, RecursionError):
                raise DemoError("invalid_json", 400) from None
            self._json(200, self.server.session.execute(request))
        except DemoError as error:
            self._json(error.status, {"error": error.code})
        except Exception:
            self._json(503, {"error": "unavailable"})


def main():
    parser = argparse.ArgumentParser(description="SIMULATED local Demo; hosted AI disabled")
    parser.add_argument("--port", type=int, default=4190)
    parser.add_argument("--build-root", type=Path, default=Path(__file__).resolve().parents[1] / "portfolio-ui" / "dist")
    args = parser.parse_args()
    server = DemoServer(("127.0.0.1", args.port), args.build_root)
    print(f"SIMULATED local runtime: {server.origin} (hosted AI disabled)", flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
