"""HTTP live-reloading dev server with SSE browser synchronization for Lantern."""

from __future__ import annotations

import http.server
import mimetypes
import os
import queue
import socket
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from lantern.compiler import LanternCompiler


def find_available_port(start_port: int = 8080, max_attempts: int = 50) -> int:
    """Find an available TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", p))
                return p
            except OSError:
                continue
    # Fallback to ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class SSEClientQueue:
    """Thread-safe queue for SSE reload signals."""

    def __init__(self) -> None:
        self.clients: list[queue.Queue[str]] = []
        self.lock = threading.Lock()

    def register(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=10)
        with self.lock:
            self.clients.append(q)
        return q

    def unregister(self, q: queue.Queue[str]) -> None:
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)

    def broadcast_reload(self) -> None:
        with self.lock:
            for q in list(self.clients):
                try:
                    q.put_nowait("reload")
                except queue.Full:
                    pass


class LanternDevHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for serving compiled document, static assets, and SSE events."""

    server_instance: LanternDevServer

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # SSE Endpoint
        if path == "/_lantern/events":
            self.handle_sse()
            return

        # Static assets endpoint
        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            self.serve_static_file(self.server_instance.compiler.static_dir / rel)
            return

        # Serve index or specific file
        if path in ("/", f"/{self.server_instance.target_file.stem}.html"):
            self.serve_compiled_html()
            return

        # Workspace relative files (e.g. images, local datasets)
        workspace_file = (self.server_instance.workspace_dir / path.lstrip("/")).resolve()
        if workspace_file.exists() and workspace_file.is_file() and str(workspace_file).startswith(str(self.server_instance.workspace_dir)):
            self.serve_static_file(workspace_file)
            return

        self.send_error(404, f"File Not Found: {path}")

    def handle_sse(self) -> None:
        """Stream Server-Sent Events to keep browser in sync."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = self.server_instance.sse_hub.register()
        try:
            # Initial ping
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()

            while not self.server_instance.stop_event.is_set():
                try:
                    msg = q.get(timeout=1.0)
                    if msg == "reload":
                        payload = b"data: reload\n\n"
                        self.wfile.write(payload)
                        self.wfile.flush()
                except queue.Empty:
                    # Keep-alive heartbeat comment
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.server_instance.sse_hub.unregister(q)

    def serve_compiled_html(self) -> None:
        """Compile Markdown on demand and serve with live-reload enabled."""
        try:
            html_text = self.server_instance.get_latest_html()
            encoded = html_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(encoded)
        except Exception as exc:
            err_msg = f"Lantern Compilation Error:\n{exc}".encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(err_msg)))
            self.end_headers()
            self.wfile.write(err_msg)

    def serve_static_file(self, file_path: Path) -> None:
        """Serve a static asset with correct MIME type."""
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, f"Asset Not Found: {file_path.name}")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"

        try:
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self.send_error(500, f"Error reading asset: {exc}")

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress routine GET logging unless error
        if args and str(args[0]).startswith(("4", "5")):
            super().log_message(format, *args)


class WorkspaceWatcher(FileSystemEventHandler):
    """Watches markdown file, referenced python scripts, and templates for changes."""

    def __init__(self, server: LanternDevServer) -> None:
        self.server = server
        self.last_trigger = 0.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        src_path = Path(event.src_path).resolve()
        # Filter files of interest (.md, .py, .j2, .css, .js)
        if src_path.suffix not in (".md", ".py", ".j2", ".css", ".js"):
            return

        now = time.time()
        # Debounce rapid file write events (150ms)
        if now - self.last_trigger < 0.15:
            return
        self.last_trigger = now

        # Trigger recompile and browser reload
        self.server.notify_change(src_path)


class LanternDevServer:
    """Live dev server coordinator."""

    def __init__(
        self,
        target_file: Path | str,
        port: int = 8080,
        host: str = "127.0.0.1",
        template_name: str = "explainer",
        compiler: LanternCompiler | None = None,
    ) -> None:
        self.target_file = Path(target_file).resolve()
        self.workspace_dir = self.target_file.parent
        self.port = find_available_port(port)
        self.host = host
        self.template_name = template_name
        self.compiler = compiler or LanternCompiler()

        self.sse_hub = SSEClientQueue()
        self.stop_event = threading.Event()
        self.cached_html: str | None = None
        self.observer: Observer | None = None
        self.httpd: http.server.ThreadingHTTPServer | None = None

    def get_latest_html(self) -> str:
        """Compile document on demand or return cached version."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target document not found: {self.target_file}")

        text = self.target_file.read_text(encoding="utf-8")
        self.cached_html = self.compiler.compile(
            markdown_text=text,
            template_name=self.template_name,
            standalone=False,
            base_dir=self.workspace_dir,
            live_reload=True,
        )
        return self.cached_html

    def notify_change(self, changed_path: Path) -> None:
        """Called by watchdog when a watched file changes."""
        try:
            self.get_latest_html()
            self.sse_hub.broadcast_reload()
            print(f"\033[36m[Lantern]\033[0m Modified: {changed_path.name} → Reloading browser")
        except Exception as e:
            print(f"\033[31m[Lantern] Recompile Error:\033[0m {e}", file=sys.stderr)

    def start(self, open_browser: bool = True) -> None:
        """Start watcher and HTTP server."""
        # Initial compile to extract referenced python scripts
        self.get_latest_html()

        # Start watchdog
        self.observer = Observer()
        handler = WorkspaceWatcher(self)
        self.observer.schedule(handler, str(self.workspace_dir), recursive=True)

        # Also watch templates and static dir
        if self.compiler.template_dir.exists():
            self.observer.schedule(handler, str(self.compiler.template_dir), recursive=True)
        if self.compiler.static_dir.exists():
            self.observer.schedule(handler, str(self.compiler.static_dir), recursive=True)

        self.observer.start()

        # Start HTTP server
        handler_cls = type(
            "LanternBoundHandler",
            (LanternDevHandler,),
            {"server_instance": self},
        )
        self.httpd = http.server.ThreadingHTTPServer((self.host, self.port), handler_cls)

        url = f"http://{self.host}:{self.port}"

        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()

        try:
            self.httpd.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shut down dev server."""
        self.stop_event.set()
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
