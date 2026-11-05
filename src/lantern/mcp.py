"""Model Context Protocol (MCP) server for Lantern."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from lantern import __version__
from lantern.compiler import LanternCompiler
from lantern.config import SiteConfig
from lantern.scaffold import create_project
from lantern.site import LanternSiteBuilder

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "lantern_build",
        "description": "Compiles Markdown explainers, simulation dashboards, or multi-page sites via Lantern into optimized HTML assets or export packages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to input markdown document (.md), content directory, or site manifest (site.yaml).",
                },
                "out_dir": {
                    "type": "string",
                    "description": "Target output directory or HTML file path (default: 'dist').",
                    "default": "dist",
                },
                "standalone": {
                    "type": "boolean",
                    "description": "Inline all CSS, KaTeX math fonts, and JavaScript into a single self-contained HTML file (default: true).",
                    "default": True,
                },
                "template": {
                    "type": "string",
                    "description": "Layout template name ('explainer', 'dashboard', 'optimization', etc., default: 'explainer').",
                    "default": "explainer",
                },
                "format": {
                    "type": "string",
                    "description": "Build or export format: 'static' or 'jinja' (default: 'static').",
                    "default": "static",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "lantern_serve",
        "description": "Launches the live-reloading interactive explainer and dashboard preview server via Lantern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Target Markdown document (.md), content directory, or site manifest (site.yaml).",
                },
                "port": {
                    "type": "integer",
                    "description": "Dev server HTTP port (default: 8080).",
                    "default": 8080,
                },
                "host": {
                    "type": "string",
                    "description": "Dev server HTTP host (default: '127.0.0.1').",
                    "default": "127.0.0.1",
                },
                "no_open": {
                    "type": "boolean",
                    "description": "Do not automatically open browser on launch (default: true).",
                    "default": True,
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "lantern_new",
        "description": "Scaffolds a new interactive explainer, simulation dashboard, or optimization lab workspace via Lantern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the workspace directory to create.",
                },
                "template": {
                    "type": "string",
                    "description": "Starter template: 'explainer' (default), 'dashboard', or 'optimization'.",
                    "default": "explainer",
                },
            },
            "required": ["name"],
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a Lantern MCP tool call and return JSON-serializable results."""
    try:
        if name == "lantern_build":
            path_str = arguments.get("path")
            if not path_str or not isinstance(path_str, str) or not path_str.strip():
                return {"status": "error", "error": "Missing or empty 'path' argument."}

            target = Path(path_str).expanduser().resolve()
            if not target.exists():
                return {"status": "error", "error": f"Path not found: {target}"}

            out_dir_str = arguments.get("out_dir", "dist") or "dist"
            out = Path(out_dir_str).expanduser()
            if not out.is_absolute():
                out = (target if target.is_dir() else target.parent) / out

            template = arguments.get("template", "explainer") or "explainer"
            raw_standalone = arguments.get("standalone", True)
            if isinstance(raw_standalone, str):
                standalone = raw_standalone.lower() not in ("false", "0", "no")
            else:
                standalone = bool(raw_standalone)

            fmt = (arguments.get("format", "static") or "static").lower()
            compiler = LanternCompiler()

            if fmt == "jinja":
                out_path = compiler.export_jinja(
                    input_path=target,
                    output_dir=out,
                    template_name=template,
                )
                files = [str(p.relative_to(out_path)) for p in out_path.rglob("*") if p.is_file()]
                return {
                    "status": "ok",
                    "format": "jinja",
                    "target": str(target),
                    "output_dir": str(out_path),
                    "file_count": len(files),
                    "files": files,
                }

            is_site = target.is_dir() or target.name in ("site.yaml", "site.yml")
            if is_site:
                site_config = SiteConfig.load(target=target, output_dir=out)
                if template:
                    site_config.template = template
                builder = LanternSiteBuilder()
                out_dir_path = builder.build(site_config=site_config, standalone=standalone)
                html_files = [str(p.relative_to(out_dir_path)) for p in out_dir_path.rglob("*.html")]
                return {
                    "status": "ok",
                    "site_name": site_config.site_name,
                    "target": str(target),
                    "output_dir": str(out_dir_path),
                    "page_count": len(site_config.pages),
                    "pages": [p.rel_html_path for p in site_config.pages],
                    "standalone": standalone,
                }

            # Single document compilation
            if out.suffix == ".html":
                out_file = out
            else:
                out_file = out / f"{target.stem}.html"

            out_file.parent.mkdir(parents=True, exist_ok=True)
            result_file = compiler.compile_file(
                input_path=target,
                output_path=out_file,
                template_name=template,
                standalone=standalone,
            )

            return {
                "status": "ok",
                "target": str(target),
                "output": str(result_file),
                "output_file": str(result_file),
                "output_dir": str(result_file.parent),
                "size_bytes": result_file.stat().st_size,
                "template": template,
                "standalone": standalone,
            }

        elif name == "lantern_serve":
            path_str = arguments.get("path")
            if not path_str or not isinstance(path_str, str) or not path_str.strip():
                return {"status": "error", "error": "Missing or empty 'path' argument."}

            target = Path(path_str).expanduser().resolve()
            if not target.exists():
                return {"status": "error", "error": f"Path not found: {target}"}

            port = int(arguments.get("port", 8080))
            host = str(arguments.get("host", "127.0.0.1"))
            no_open = bool(arguments.get("no_open", True))

            env = dict(os.environ)
            src_dir = str(Path(__file__).resolve().parent.parent)
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{src_dir}:{existing_pp}" if existing_pp else src_dir

            launcher = shutil.which("lantern")
            if launcher:
                cmd = [launcher, "serve", str(target), "-p", str(port), "--host", host, "--no-color"]
            else:
                cmd = [
                    sys.executable,
                    "-m",
                    "lantern.cli",
                    "serve",
                    str(target),
                    "-p",
                    str(port),
                    "--host",
                    host,
                    "--no-color",
                ]

            if no_open:
                cmd.append("--no-open")

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=target if target.is_dir() else target.parent,
                start_new_session=True,
                env=env,
            )
            return {
                "status": "ok",
                "pid": proc.pid,
                "target": str(target),
                "url": f"http://{host}:{port}",
                "port": port,
                "host": host,
                "no_open": no_open,
            }

        elif name == "lantern_new":
            name_val = arguments.get("name", "")
            if not isinstance(name_val, str) or not name_val.strip():
                return {"status": "error", "error": "Missing or empty 'name' argument."}

            template_val = arguments.get("template", "explainer") or "explainer"
            return create_project(name=name_val, template=template_val)

        else:
            return {"status": "error", "error": f"Unknown tool: {name}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}


class StdioMCPServer:
    """JSON-RPC 2.0 stdio server implementing the Model Context Protocol."""

    def __init__(self) -> None:
        self.server_info = {"name": "lantern", "version": __version__}

    def handle_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": self.server_info,
                    "capabilities": {"tools": {}},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOL_DEFINITIONS},
            }

        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments", {})
            res = execute_tool(name, args)
            is_error = res.get("status") == "error"

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2)}],
                    "isError": is_error,
                },
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    def run(self) -> int:
        """Run JSON-RPC event loop reading lines from sys.stdin."""
        for line in sys.stdin:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                req = json.loads(line_str)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
        return 0


def main() -> int:
    """Entry point for `lantern mcp` stdio server."""
    return StdioMCPServer().run()
