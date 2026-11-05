"""Unit tests for Lantern MCP server protocol and tool execution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lantern.cli import main
from lantern.mcp import StdioMCPServer, TOOL_DEFINITIONS, execute_tool


def test_mcp_initialize() -> None:
    server = StdioMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "lantern"
    assert "version" in resp["result"]["serverInfo"]


def test_mcp_ping() -> None:
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 42, "method": "ping"}
    resp = server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 42
    assert resp["result"] == {}


def test_mcp_tools_list() -> None:
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    resp = server.handle_request(req)
    assert resp is not None
    tool_names = [t["name"] for t in resp["result"]["tools"]]
    assert "lantern_build" in tool_names
    assert "lantern_serve" in tool_names
    assert "lantern_new" in tool_names

    # Check schemas
    tools_by_name = {t["name"]: t for t in resp["result"]["tools"]}
    build_tool = tools_by_name["lantern_build"]
    assert "path" in build_tool["inputSchema"]["properties"]
    assert "out_dir" in build_tool["inputSchema"]["properties"]
    assert "standalone" in build_tool["inputSchema"]["properties"]
    assert "template" in build_tool["inputSchema"]["properties"]
    assert "format" in build_tool["inputSchema"]["properties"]
    assert build_tool["inputSchema"]["required"] == ["path"]

    serve_tool = tools_by_name["lantern_serve"]
    assert "path" in serve_tool["inputSchema"]["properties"]
    assert "port" in serve_tool["inputSchema"]["properties"]
    assert "host" in serve_tool["inputSchema"]["properties"]
    assert "no_open" in serve_tool["inputSchema"]["properties"]
    assert serve_tool["inputSchema"]["required"] == ["path"]

    new_tool = tools_by_name["lantern_new"]
    assert "name" in new_tool["inputSchema"]["properties"]
    assert "template" in new_tool["inputSchema"]["properties"]
    assert new_tool["inputSchema"]["required"] == ["name"]


def test_mcp_validation() -> None:
    # lantern_new validation
    assert execute_tool("lantern_new", {"name": ""})["status"] == "error"
    assert execute_tool("lantern_new", {})["status"] == "error"

    # lantern_build validation
    assert execute_tool("lantern_build", {"path": ""})["status"] == "error"
    assert execute_tool("lantern_build", {"path": "/nonexistent/test.md"})["status"] == "error"

    # lantern_serve validation
    assert execute_tool("lantern_serve", {"path": ""})["status"] == "error"
    assert execute_tool("lantern_serve", {"path": "/nonexistent/test.md"})["status"] == "error"


def test_mcp_execute_unknown() -> None:
    res = execute_tool("nonexistent_tool", {})
    assert res["status"] == "error"
    assert "Unknown tool" in res["error"]


def test_mcp_new_and_build(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    # 1. Test lantern_new via execute_tool
    res_new = execute_tool("lantern_new", {"name": "sample_lab", "template": "explainer"})
    assert res_new["status"] == "ok"
    proj_dir = tmp_path / "sample_lab"
    assert proj_dir.is_dir()
    explainer_file = proj_dir / "explainer.md"
    assert explainer_file.is_file()

    # 2. Test lantern_build via execute_tool
    res_build = execute_tool(
        "lantern_build",
        {
            "path": str(explainer_file),
            "out_dir": str(proj_dir / "dist"),
            "standalone": True,
            "template": "explainer",
            "format": "static",
        },
    )
    assert res_build["status"] == "ok"
    assert "output" in res_build
    out_file = Path(res_build["output"])
    assert out_file.is_file()
    assert out_file.stat().st_size > 0
    content = out_file.read_text(encoding="utf-8")
    assert "<style>" in content
    assert "Interactive Explainer" in content


def test_mcp_tools_call_jsonrpc(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    server = StdioMCPServer()

    doc = tmp_path / "simple.md"
    doc.write_text("# Test Simple Document\n\nHello from Lantern MCP test.", encoding="utf-8")

    req = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "tools/call",
        "params": {
            "name": "lantern_build",
            "arguments": {
                "path": str(doc),
                "standalone": True,
            },
        },
    }
    resp = server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 100
    assert not resp["result"]["isError"]
    content_list = resp["result"]["content"]
    assert len(content_list) == 1
    data = json.loads(content_list[0]["text"])
    assert data["status"] == "ok"
    assert Path(data["output"]).is_file()


def test_mcp_cli_help(capsys) -> None:
    ret = main(["-h"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "mcp" in captured.out
