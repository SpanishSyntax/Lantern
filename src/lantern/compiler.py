"""Markdown and Jinja2 orchestration engine for Lantern."""

from __future__ import annotations

import datetime
import importlib.resources
import os
import re
import shutil
from pathlib import Path
from typing import Any

import jinja2
import markdown

from lantern.directives import LanternExtension


class LanternCompiler:
    """Compiles Markdown documents into interactive scientific explainers and simulation dashboards."""

    def __init__(
        self,
        template_dir: Path | str | None = None,
        static_dir: Path | str | None = None,
    ) -> None:
        if template_dir is not None:
            self.template_dir = Path(template_dir).resolve()
        else:
            try:
                pkg_templates = importlib.resources.files("lantern").joinpath("templates")
                self.template_dir = Path(str(pkg_templates))
            except Exception:
                self.template_dir = Path(__file__).parent / "templates"

        if static_dir is not None:
            self.static_dir = Path(static_dir).resolve()
        else:
            try:
                pkg_static = importlib.resources.files("lantern").joinpath("static")
                self.static_dir = Path(str(pkg_static))
            except Exception:
                self.static_dir = Path(__file__).parent / "static"

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

        self.watched_scripts: set[Path] = set()
        self.has_plotly = False

    def reset_state(self) -> None:
        """Reset per-compilation tracking flags."""
        self.watched_scripts.clear()
        self.has_plotly = False

    def register_watched_script(self, script_path: Path) -> None:
        """Register a Python script referenced by ::: plot directive."""
        self.watched_scripts.add(script_path.resolve())

    def parse_frontmatter(self, text: str) -> tuple[dict[str, Any], str]:
        """Extract YAML-style frontmatter delimited by ---."""
        fm: dict[str, Any] = {}
        content = text

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                raw_fm = parts[1]
                content = parts[2]
                for line in raw_fm.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if v.lower() == "true":
                            fm[k] = True
                        elif v.lower() == "false":
                            fm[k] = False
                        else:
                            fm[k] = v

        return fm, content

    def extract_title(self, content: str, default: str = "Lantern Explainer") -> str:
        """Extract document title from the first H1 header if not provided in frontmatter."""
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return default

    def _protect_math(self, text: str) -> tuple[str, list[str]]:
        """Protect KaTeX math ($...$ and $$...$$) from markdown parser transforms."""
        placeholders: list[str] = []

        def repl_display(match: re.Match[str]) -> str:
            idx = len(placeholders)
            placeholders.append(match.group(0))
            return f"KATEXDISPLAYMATHPLACEHOLDER{idx}END"

        def repl_inline(match: re.Match[str]) -> str:
            idx = len(placeholders)
            placeholders.append(match.group(0))
            return f"KATEXINLINEMATHPLACEHOLDER{idx}END"

        # Display math first ($$ ... $$)
        text = re.sub(r"\$\$([\s\S]*?)\$\$", repl_display, text)
        # Inline math ($ ... $) with non-space boundary
        text = re.sub(r"(?<!\\)\$(?!\s)([^\$\n]+?)(?<!\s)\$", repl_inline, text)

        return text, placeholders

    MATH_RESTORE_RE = re.compile(r"KATEX(DISPLAY|INLINE)MATHPLACEHOLDER(\d+)END")

    def _restore_math(self, html_text: str, placeholders: list[str]) -> str:
        """Restore protected KaTeX math placeholders into output HTML in linear O(M) time."""
        if not placeholders:
            return html_text

        def _repl(match: re.Match[str]) -> str:
            idx = int(match.group(2))
            if 0 <= idx < len(placeholders):
                return placeholders[idx]
            return match.group(0)

        return self.MATH_RESTORE_RE.sub(_repl, html_text)

    def _read_static_asset(self, relative_path: str) -> str:
        """Read content of a static file for standalone inlining."""
        file_path = self.static_dir / relative_path
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""

    def compile(
        self,
        markdown_text: str,
        template_name: str = "explainer",
        standalone: bool = False,
        base_dir: Path | None = None,
        live_reload: bool = False,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Compile Markdown string to full HTML document."""
        self.reset_state()
        base_dir = Path(base_dir or os.getcwd()).resolve()

        frontmatter, content = self.parse_frontmatter(markdown_text)

        # Allow frontmatter to override template / standalone
        if "template" in frontmatter:
            template_name = str(frontmatter["template"])
        if "standalone" in frontmatter:
            standalone = bool(frontmatter["standalone"])

        title = frontmatter.get("title") or self.extract_title(content)
        subtitle = frontmatter.get("subtitle", "")
        author = frontmatter.get("author", "")
        date = frontmatter.get("date", datetime.date.today().isoformat())
        snowpack_pdf = frontmatter.get("snowpack_pdf", "")

        # Protect math delimiters
        protected_content, math_placeholders = self._protect_math(content)

        # Markdown Parser configuration with all scientific directives
        ext = LanternExtension(compiler=self, base_dir=base_dir)
        md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "tables",
                "toc",
                "attr_list",
                "def_list",
                ext,
            ]
        )

        raw_html = md.convert(protected_content)
        rendered_content = self._restore_math(raw_html, math_placeholders)

        # Prepare Template Context
        context: dict[str, Any] = {
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "date": date,
            "snowpack_pdf": snowpack_pdf,
            "content": rendered_content,
            "standalone": standalone,
            "live_reload": live_reload,
            "static_prefix": "/static",
            "has_plotly": self.has_plotly,
        }

        # Embed static assets if standalone mode requested
        if standalone:
            context["lantern_css"] = self._read_static_asset("lantern.css")
            context["lantern_js"] = self._read_static_asset("lantern.js")
            context["katex_css"] = self._read_static_asset("katex/katex.min.css")
            context["katex_js"] = self._read_static_asset("katex/katex.min.js")
            context["katex_auto_render_js"] = self._read_static_asset("katex/contrib/auto-render.min.js")

        if extra_context:
            context.update(extra_context)

        # Choose template
        template_file = f"{template_name}.html.j2"
        if not (self.template_dir / template_file).exists():
            template_file = "explainer.html.j2"

        template = self.jinja_env.get_template(template_file)
        return template.render(**context)

    def compile_file(
        self,
        input_path: Path | str,
        output_path: Path | str | None = None,
        template_name: str = "explainer",
        standalone: bool = False,
        live_reload: bool = False,
    ) -> Path:
        """Compile a markdown file and write the resulting HTML to disk."""
        in_file = Path(input_path).resolve()
        if not in_file.exists():
            raise FileNotFoundError(f"Input Markdown file not found: {in_file}")

        text = in_file.read_text(encoding="utf-8")
        html_out = self.compile(
            markdown_text=text,
            template_name=template_name,
            standalone=standalone,
            base_dir=in_file.parent,
            live_reload=live_reload,
        )

        if output_path is None:
            out_file = in_file.with_suffix(".html")
        else:
            out_p = Path(output_path).resolve()
            if out_p.is_dir() or str(output_path).endswith(("/", "\\")):
                out_p.mkdir(parents=True, exist_ok=True)
                out_file = out_p / f"{in_file.stem}.html"
            else:
                out_p.parent.mkdir(parents=True, exist_ok=True)
                out_file = out_p

        out_file.write_text(html_out, encoding="utf-8")
        return out_file

    def export_static(
        self,
        input_path: Path | str,
        output_dir: Path | str | None = None,
        template_name: str = "explainer",
    ) -> Path:
        """Export a self-contained static web bundle ready for production hosting.

        Emits:
        - index.html with relative ./static asset links
        - static/ directory containing lantern.css, lantern.js, and katex/
        - Any referenced python scripts and local media assets
        - README.md with production deployment guidance (Nginx, Caddy, Cloudflare, S3)
        """
        in_file = Path(input_path).resolve()
        if not in_file.exists():
            raise FileNotFoundError(f"Input Markdown file not found: {in_file}")

        if output_dir is None:
            out_dir = in_file.parent / "dist" / f"{in_file.stem}_static"
        else:
            out_dir = Path(output_dir).resolve()

        out_dir.mkdir(parents=True, exist_ok=True)

        text = in_file.read_text(encoding="utf-8")
        html_out = self.compile(
            markdown_text=text,
            template_name=template_name,
            standalone=False,
            base_dir=in_file.parent,
            live_reload=False,
            extra_context={"static_prefix": "./static"},
        )
        (out_dir / "index.html").write_text(html_out, encoding="utf-8")

        # Copy static assets
        dest_static = out_dir / "static"
        if dest_static.exists():
            shutil.rmtree(dest_static)
        shutil.copytree(self.static_dir, dest_static)

        # Copy referenced scripts (from ::: plot directives)
        for script_path in self.watched_scripts:
            if script_path.exists() and script_path.is_file():
                try:
                    rel = script_path.relative_to(in_file.parent)
                    target = out_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(script_path, target)
                except ValueError:
                    shutil.copy2(script_path, out_dir / script_path.name)

        # Production deployment guide
        readme_content = f"""# {in_file.stem.title()} — Production Static Bundle
Compiled with **Lantern** (Frost Architecture)

This directory contains a standalone static deployment bundle ready for production hosting.
It requires zero Node.js, Python, or runtime daemon on the host.

## Quick Hosting Options

### 1. Caddy Server (Recommended)
```bash
caddy file-server --listen :8080 --root .
```

### 2. Nginx
```nginx
server {{
    listen 80;
    server_name example.com;
    root /var/www/{in_file.stem};
    index index.html;
    location / {{
        try_files $uri $uri/ =404;
    }}
}}
```

### 3. Cloudflare Pages / Netlify / Vercel / GitHub Pages
Deploy or commit the contents of this folder directly to your hosting provider.

### 4. Local Testing
```bash
python3 -m http.server 8080
```
"""
        (out_dir / "README.md").write_text(readme_content, encoding="utf-8")
        return out_dir

    def export_jinja(
        self,
        input_path: Path | str,
        output_dir: Path | str | None = None,
        template_name: str = "explainer",
    ) -> Path:
        """Export a standalone, production-ready Jinja2 web application project.

        Emits:
        - app.py (WSGI/HTTP production server using Jinja2 & Markdown)
        - templates/ (Jinja2 templates)
        - content/ (source markdown and python plot scripts)
        - static/ (lantern.css, lantern.js, katex/)
        - requirements.txt (jinja2, markdown, gunicorn)
        - Dockerfile (production container)
        - README.md (production operations manual)
        """
        in_file = Path(input_path).resolve()
        if not in_file.exists():
            raise FileNotFoundError(f"Input Markdown file not found: {in_file}")

        if output_dir is None:
            out_dir = in_file.parent / "dist" / f"{in_file.stem}_jinja"
        else:
            out_dir = Path(output_dir).resolve()

        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Templates directory
        dest_templates = out_dir / "templates"
        if dest_templates.exists():
            shutil.rmtree(dest_templates)
        shutil.copytree(self.template_dir, dest_templates)

        # 2. Static directory
        dest_static = out_dir / "static"
        if dest_static.exists():
            shutil.rmtree(dest_static)
        shutil.copytree(self.static_dir, dest_static)

        # 3. Content directory
        content_dir = out_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(in_file, content_dir / in_file.name)

        # Copy referenced scripts
        for script_path in self.watched_scripts:
            if script_path.exists() and script_path.is_file():
                shutil.copy2(script_path, content_dir / script_path.name)

        # 4. requirements.txt
        reqs = "jinja2>=3.1.2\nmarkdown>=3.5.0\ngunicorn>=21.2.0\n"
        (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")

        # 5. Dockerfile
        dockerfile = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
ENV PORT=8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
"""
        (out_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8")

        # 6. app.py — Standalone WSGI application runnable via gunicorn or python app.py
        app_py = f'''"""Production Jinja2 web application for {in_file.name}.
Auto-generated by Lantern Export.
"""

from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Callable

import jinja2
import markdown

BASE_DIR = Path(__file__).parent.resolve()
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
CONTENT_DIR = BASE_DIR / "content"
DOC_FILE = CONTENT_DIR / "{in_file.name}"
DEFAULT_TEMPLATE = "{template_name}"

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    fm: dict[str, Any] = {{}}
    content = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip("\'"\\\"")
            content = parts[2]
    return fm, content


def render_document() -> str:
    if not DOC_FILE.exists():
        return f"<h1>Error: {{DOC_FILE.name}} not found</h1>"

    text = DOC_FILE.read_text(encoding="utf-8")
    fm, content = parse_frontmatter(text)

    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "attr_list", "def_list"])
    html_content = md.convert(content)

    tmpl_name = fm.get("template", DEFAULT_TEMPLATE)
    tmpl_file = f"{{tmpl_name}}.html.j2"
    if not (TEMPLATES_DIR / tmpl_file).exists():
        tmpl_file = "explainer.html.j2"

    template = jinja_env.get_template(tmpl_file)
    return template.render(
        title=fm.get("title", "{in_file.stem.title()}"),
        subtitle=fm.get("subtitle", ""),
        author=fm.get("author", "Frost Research"),
        date=fm.get("date", ""),
        content=html_content,
        standalone=False,
        live_reload=False,
        static_prefix="/static",
        has_plotly=False,
    )


def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
    path: str = environ.get("PATH_INFO", "/") or "/"

    if path == "/" or path == "/index.html":
        body = render_document().encode("utf-8")
        start_response("200 OK", [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "public, max-age=300"),
        ])
        return [body]

    if path.startswith("/static/"):
        rel = path[len("/static/"):]
        target = (STATIC_DIR / rel).resolve()
        if target.exists() and target.is_file() and str(target).startswith(str(STATIC_DIR)):
            mime_type, _ = mimetypes.guess_type(str(target))
            mime_type = mime_type or "application/octet-stream"
            content = target.read_bytes()
            start_response("200 OK", [
                ("Content-Type", mime_type),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "public, max-age=86400"),
            ])
            return [content]

    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not Found"]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = int(os.environ.get("PORT", 8080))
    print(f"Serving on http://127.0.0.1:{{port}} (Press Ctrl+C to stop)...")
    server = make_server("0.0.0.0", port, app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
'''
        (out_dir / "app.py").write_text(app_py, encoding="utf-8")

        # 7. README.md
        readme_jinja = f"""# {in_file.stem.title()} — Production Jinja2 Project
Generated with **Lantern** (Frost Architecture)

This is a complete, self-contained Python Jinja2 WSGI application ready for production deployment.

## Running Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
Open `http://127.0.0.1:8080`.

## Production Deployment with Gunicorn
```bash
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## Production Deployment with Docker
```bash
docker build -t {in_file.stem}-app .
docker run -p 8080:8080 {in_file.stem}-app
```
"""
        (out_dir / "README.md").write_text(readme_jinja, encoding="utf-8")
        return out_dir
