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
from lantern.config import PageMeta, SiteConfig


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

        # Multi-page site handling
        if self.server_instance.is_site:
            target_rel: str | None = None
            if path in ("/", "/index.html"):
                target_rel = "index.html"
            else:
                clean = path.lstrip("/")
                if not clean.endswith(".html") and "." not in Path(clean).name:
                    clean = f"{clean}.html"
                assert self.server_instance.site_config is not None
                for p in self.server_instance.site_config.pages:
                    if p.rel_html_path == clean:
                        target_rel = clean
                        break

            if target_rel is not None:
                self.serve_compiled_site_page(target_rel)
                return

            # Check files in root_dir or content_dir (plots, styles, images, companion pdf)
            assert self.server_instance.site_config is not None
            search_dirs = [
                self.server_instance.workspace_dir,
                self.server_instance.site_config.content_dir,
            ]
            for s_dir in search_dirs:
                cand = (s_dir / path.lstrip("/")).resolve()
                if cand.exists() and cand.is_file() and str(cand).startswith(str(s_dir)):
                    self.serve_static_file(cand)
                    return

            self.send_error(404, f"File Not Found: {path}")
            return

        # Single file mode
        assert self.server_instance.target_file is not None
        if path in ("/", f"/{self.server_instance.target_file.stem}.html"):
            self.serve_compiled_html()
            return

        # Workspace relative files (e.g. images, local datasets)
        workspace_file = (self.server_instance.workspace_dir / path.lstrip("/")).resolve()
        if (
            workspace_file.exists()
            and workspace_file.is_file()
            and str(workspace_file).startswith(str(self.server_instance.workspace_dir))
        ):
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

    def serve_compiled_site_page(self, rel_html_path: str) -> None:
        """Compile specific page on demand for multi-page site."""
        try:
            html_text = self.server_instance.get_page_html(rel_html_path)
            encoded = html_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(encoded)
        except Exception as exc:
            err_msg = f"Lantern Multi-Page Error ({rel_html_path}):\n{exc}".encode("utf-8")
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
    """Watches markdown file, referenced python scripts, styles, and templates for changes."""

    VALID_EXTENSIONS = {".md", ".py", ".j2", ".css", ".js", ".yaml", ".yml"}
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
    """Live dev server coordinator supporting single-page and multi-page sites."""

    def __init__(
        self,
        target_file: Path | str,
        port: int = 8080,
        host: str = "127.0.0.1",
        template_name: str = "explainer",
        compiler: LanternCompiler | None = None,
    ) -> None:
        target_p = Path(target_file).resolve()
        self.target_orig = target_p
        self.compiler = compiler or LanternCompiler()

        if target_p.is_dir() or target_p.name in ("site.yaml", "site.yml"):
            self.is_site = True
            self.site_config = SiteConfig.load(target_p)
            self.workspace_dir = self.site_config.root_dir
            self.target_file = None
            self.template_name = self.site_config.template or template_name
        else:
            self.is_site = False
            self.site_config = None
            self.target_file = target_p
            self.workspace_dir = self.target_file.parent
            self.template_name = template_name

        self.port = find_available_port(port)
        self.host = host
        self.sse_hub = SSEClientQueue()
        self.stop_event = threading.Event()
        self.cached_html: str | None = None
        self.observer: Observer | None = None
        self.httpd: http.server.ThreadingHTTPServer | None = None

    def _read_file_safe(self, path: Path) -> str:
        """Retry reading file with brief backoff for atomic editor saves."""
        for attempt in range(5):
            if path.exists():
                try:
                    raw = path.read_text(encoding="utf-8")
                    if len(raw) == 0 and attempt < 4:
                        time.sleep(0.04)
                        continue
                    return raw
                except (OSError, PermissionError):
                    time.sleep(0.04)
            else:
                time.sleep(0.04)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_text(encoding="utf-8")

    def get_latest_html(self) -> str:
        """Compile document on demand or return cached version (single file mode)."""
        if self.target_file is None:
            return ""
        text = self._read_file_safe(self.target_file)
        self.cached_html = self.compiler.compile(
            markdown_text=text,
            template_name=self.template_name,
            standalone=False,
            base_dir=self.workspace_dir,
            live_reload=True,
            input_path=self.target_file,
        )
        return self.cached_html

    def get_page_html(self, rel_html_path: str) -> str:
        """Compile specific page on demand for multi-page site."""
        if not self.site_config:
            raise ValueError("DevServer is not configured for a multi-page site.")

        matching_page: PageMeta | None = None
        for p in self.site_config.pages:
            if p.rel_html_path == rel_html_path:
                matching_page = p
                break

        if matching_page is None:
            # Check if index.html can fall back to first page
            if rel_html_path == "index.html" and self.site_config.pages:
                matching_page = self.site_config.pages[0]
            else:
                raise FileNotFoundError(f"Page not found in navigation: {rel_html_path}")

        text = self._read_file_safe(matching_page.src_path)

        # Collect global extra CSS
        extra_css_parts: list[str] = []
        for css_rel in self.site_config.extra_css:
            css_p = (self.site_config.root_dir / css_rel).resolve()
            if css_p.exists() and css_p.is_file():
                extra_css_parts.append(css_p.read_text(encoding="utf-8"))
        extra_css_content = "\n".join(extra_css_parts) if extra_css_parts else ""

        # Calculate root_path relative prefix
        rel_parts = Path(matching_page.rel_html_path).parent.parts
        root_path = ("../" * len(rel_parts)) if (rel_parts and rel_parts != (".",)) else ""

        # Adjust breadcrumbs
        adjusted_crumbs: list[dict[str, str | None]] = []
        for crumb in matching_page.breadcrumbs:
            c_url = crumb.get("url")
            adjusted_crumbs.append({
                "title": str(crumb["title"]),
                "url": f"{root_path}{c_url}" if c_url else None,
            })

        # Adjust prev / next
        adj_prev = None
        if matching_page.prev_page:
            adj_prev = {
                "title": matching_page.prev_page["title"],
                "url": f"{root_path}{matching_page.prev_page['url']}",
            }

        adj_next = None
        if matching_page.next_page:
            adj_next = {
                "title": matching_page.next_page["title"],
                "url": f"{root_path}{matching_page.next_page['url']}",
            }

        # Sibling CSS
        sibling_css = None
        if matching_page.sibling_css_path and matching_page.sibling_css_path.exists():
            sibling_css = matching_page.sibling_css_path.read_text(encoding="utf-8")

        extra_ctx = {
            "site_name": self.site_config.site_name,
            "brand": self.site_config.brand,
            "brand_icon": self.site_config.brand_icon,
            "snowpack_pdf": self.site_config.snowpack_pdf,
            "root_path": root_path,
            "breadcrumbs": adjusted_crumbs,
            "prev_page": adj_prev,
            "next_page": adj_next,
            "extra_css_content": extra_css_content,
            "sibling_css": sibling_css,
            "static_prefix": f"{root_path}static",
        }

        return self.compiler.compile(
            markdown_text=text,
            template_name=self.site_config.template,
            standalone=False,
            base_dir=matching_page.src_path.parent,
            live_reload=True,
            extra_context=extra_ctx,
            input_path=matching_page.src_path,
            rewrite_md_links=True,
        )

    def notify_change(self, changed_path: Path) -> None:
        """Called by watchdog when a watched file changes."""
        try:
            if self.is_site:
                if changed_path.name in ("site.yaml", "site.yml"):
                    self.site_config = SiteConfig.load(self.target_orig)
                self.sse_hub.broadcast_reload()
                print(f"\033[36m[Lantern]\033[0m Modified: {changed_path.name} → Reloading browser")
            else:
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
                            if self.is_site:
                                self.sse_hub.broadcast_reload()
                            else:
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
        if not self.is_site:
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
        self.port = self.httpd.server_address[1]

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
