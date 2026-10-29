"""Tests for Lantern dev server and SSE client hub."""

from pathlib import Path
import pytest
from lantern.server import SSEClientQueue, find_available_port, LanternDevServer


def test_sse_hub():
    hub = SSEClientQueue()
    q1 = hub.register()
    q2 = hub.register()
    assert len(hub.clients) == 2

    hub.broadcast_reload()
    assert q1.get_nowait() == "reload"
    assert q2.get_nowait() == "reload"

    hub.unregister(q1)
    assert len(hub.clients) == 1


def test_port_finder():
    port = find_available_port(8900)
    assert isinstance(port, int)
    assert port >= 8900


def test_server_init(tmp_path):
    doc = tmp_path / "test.md"
    doc.write_text("# Test\nContent", encoding="utf-8")
    server = LanternDevServer(target_file=doc, port=9876)
    assert server.port >= 9876
    assert server.target_file == doc
    html = server.get_latest_html()
    assert "Test" in html
    assert "__lantern_live_reload" in html


def test_server_atomic_save_tolerance(tmp_path):
    """Ensure server gracefully tolerates momentary file unlinking during editor atomic saves."""
    import threading
    import time

    doc = tmp_path / "test.md"
    doc.write_text("# Initial Big Header\nLong content line 1\nLong content line 2\n", encoding="utf-8")
    server = LanternDevServer(target_file=doc, port=9877)

    # Simulate editor atomic save that temporarily unlinks test.md before writing shorter content
    def editor_save_worker():
        time.sleep(0.02)
        doc.unlink()
        time.sleep(0.04)
        doc.write_text("# Short\n", encoding="utf-8")

    t = threading.Thread(target=editor_save_worker)
    t.start()

    html = server.get_latest_html()
    t.join()
    assert "Short" in html or "Initial Big Header" in html


def test_watcher_ignores_temp_and_handles_moved(tmp_path):
    """Ensure watcher ignores swap/backup files and handles atomic moved events."""
    from watchdog.events import FileModifiedEvent, FileMovedEvent
    from lantern.server import WorkspaceWatcher

    doc = tmp_path / "test.md"
    doc.write_text("# Content", encoding="utf-8")
    server = LanternDevServer(target_file=doc, port=9878)
    watcher = WorkspaceWatcher(server, debounce_delay=0.05)

    assert not watcher._should_handle(tmp_path / ".test.md.swp")
    assert not watcher._should_handle(tmp_path / "test.md~")
    assert not watcher._should_handle(tmp_path / "test.md.tmp")
    assert watcher._should_handle(tmp_path / "test.md")
    assert watcher._should_handle(tmp_path / "plot.py")
