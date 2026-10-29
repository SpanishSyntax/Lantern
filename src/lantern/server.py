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

    VALID_EXTENSIONS = {".md", ".py", ".j2", ".css", ".js"}
    IGNORE_PREFIXES = {".", "#", "___jb_"}
    IGNORE_SUFFIXES = {"~", ".tmp", ".swp", ".swo", ".bak", ".crswap"}

    def __init__(self, server: LanternDevServer, debounce_delay: float = 0.15) -> None:
        self.server = server
        self.debounce_delay = debounce_delay
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._pending_path: Path | None = None

    def _should_handle(self, path: Path) -> bool:
        name = path.name
        # Ignore temporary, swap, and editor backup files
        if any(name.startswith(pre) for pre in self.IGNORE_PREFIXES):
            return False
        if any(name.endswith(suf) for suf in self.IGNORE_SUFFIXES):
            return False
        return path.suffix in self.VALID_EXTENSIONS

    def _schedule_notify(self, target_path: Path) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._pending_path = target_path
            self._timer = threading.Timer(self.debounce_delay, self._dispatch)
            self._timer.daemon = True
            self._timer.start()

    def _dispatch(self) -> None:
        with self._lock:
            target = self._pending_path
            self._timer = None
            self._pending_path = None
        if target is not None:
            self.server.notify_change(target)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path).resolve()
        if self._should_handle(p):
            self._schedule_notify(p)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path).resolve()
        if self._should_handle(p):
            self._schedule_notify(p)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        dest_p = Path(getattr(event, "dest_path", event.src_path)).resolve()
        if self._should_handle(dest_p):
            self._schedule_notify(dest_p)


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
        """Compile document on demand or return cached version with atomic save tolerance."""
        # Retry with brief backoff in case of editor atomic file replacement / inode swap
        text = None
        for attempt in range(5):
            if self.target_file.exists():
                try:
                    raw = self.target_file.read_text(encoding="utf-8")
                    # If file was truncated to 0 bytes momentarily during editor save, wait briefly
                    if len(raw) == 0 and attempt < 4:
                        time.sleep(0.04)
                        continue
                    text = raw
                    break
                except (OSError, PermissionError):
                    time.sleep(0.04)
            else:
                time.sleep(0.04)

        if text is None:
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

    def _listen_keyboard(self, url: str) -> None:
        """Non-blocking background keystroke listener for dev server controls."""
        if not sys.stdin.isatty():
            return

        try:
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
        except Exception:
            return

        try:
            tty.setcbreak(fd)
            while not self.stop_event.is_set():
                r, _, _ = select.select([sys.stdin], [], [], 0.3)
                if r and not self.stop_event.is_set():
                    ch = sys.stdin.read(1)
                    if ch in ("q", "Q", "\x03"):  # 'q' or Ctrl+C
                        self.stop_event.set()
                        if self.httpd:
                            threading.Thread(target=self.httpd.shutdown, daemon=True).start()
                        break
                    elif ch in ("r", "R"):
                        try:
                            self.get_latest_html()
                            self.sse_hub.broadcast_reload()
                            print("\r\033[K\033[36m[Lantern]\033[0m Manual refresh triggered → Reloading browser")
                        except Exception as e:
                            print(f"\r\033[K\033[31m[Lantern] Refresh Error:\033[0m {e}", file=sys.stderr)
                    elif ch in ("o", "O"):
                        webbrowser.open(url)
                        print(f"\r\033[K\033[36m[Lantern]\033[0m Opened {url} in browser")
        except Exception:
            pass
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    def start(self, open_browser: bool = True) -> None:
        """Start watcher and HTTP server."""
        # Initial compile to extract referenced python scripts
        self.get_latest_html()

        # Start watchdog on workspace directory
        self.observer = Observer()
        handler = WorkspaceWatcher(self)
        self.observer.schedule(handler, str(self.workspace_dir), recursive=True)

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

        # Start keyboard listener in background daemon thread
        kb_thread = threading.Thread(target=self._listen_keyboard, args=(url,), daemon=True)
        kb_thread.start()

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
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            self.httpd = None
