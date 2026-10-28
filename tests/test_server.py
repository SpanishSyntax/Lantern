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
