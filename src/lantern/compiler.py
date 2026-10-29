"""Markdown and Jinja2 orchestration engine for Lantern."""

from __future__ import annotations

import datetime
import importlib.resources
import os
import re
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

    def _restore_math(self, html_text: str, placeholders: list[str]) -> str:
        """Restore protected KaTeX math placeholders into output HTML."""
        for idx, orig in enumerate(placeholders):
            html_text = html_text.replace(f"KATEXDISPLAYMATHPLACEHOLDER{idx}END", orig)
            html_text = html_text.replace(f"KATEXINLINEMATHPLACEHOLDER{idx}END", orig)
        return html_text

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
