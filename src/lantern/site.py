"""Multi-page explorable site compiler for Lantern."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from lantern.compiler import LanternCompiler
from lantern.config import PageMeta, SiteConfig


class LanternSiteBuilder:
    """Compiles a complete multi-page explorable site from a site.yaml manifest or directory tree."""

    def __init__(self, compiler: LanternCompiler | None = None) -> None:
        self.compiler = compiler or LanternCompiler()

    def build(
        self,
        site_config: SiteConfig | None = None,
        target: Path | str | None = None,
        output_dir: Path | str | None = None,
        standalone: bool = False,
        live_reload: bool = False,
    ) -> Path:
        """Compile all pages in the site manifest or directory and emit a clean static distribution."""
        config = site_config or SiteConfig.load(target=target, output_dir=output_dir)
        out_dir = Path(output_dir).resolve() if output_dir else config.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Collect global extra CSS contents
        extra_css_parts: list[str] = []
        for css_rel in config.extra_css:
            css_path = (config.root_dir / css_rel).resolve()
            if css_path.exists() and css_path.is_file():
                extra_css_parts.append(css_path.read_text(encoding="utf-8"))
                self.compiler.register_watched_script(css_path)
                # Also copy to dist if not standalone
                if not standalone:
                    dest_css = out_dir / css_rel
                    dest_css.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(css_path, dest_css)

        extra_css_content = "\n".join(extra_css_parts) if extra_css_parts else ""

        # 2. Deploy static core assets (lantern.css, lantern.js, katex)
        dest_static = out_dir / "static"
        if not standalone:
            if dest_static.exists():
                shutil.rmtree(dest_static)
            shutil.copytree(self.compiler.static_dir, dest_static)

        # 3. Copy companion PDF if specified and present
        if config.snowpack_pdf:
            pdf_path = (config.root_dir / config.snowpack_pdf).resolve()
            if pdf_path.exists() and pdf_path.is_file():
                dest_pdf = out_dir / config.snowpack_pdf
                dest_pdf.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdf_path, dest_pdf)

        # 4. Copy plots/ folder if it exists in root_dir
        plots_dir = config.root_dir / "plots"
        if plots_dir.exists() and plots_dir.is_dir():
            dest_plots = out_dir / "plots"
            if dest_plots.exists():
                shutil.rmtree(dest_plots)
            shutil.copytree(plots_dir, dest_plots)

        # 5. Copy non-markdown, non-css media assets from content_dir
        media_exts = {
            ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
            ".json", ".csv", ".pdf", ".mp4", ".webm", ".wasm",
        }
        if config.content_dir.exists():
            for root, _, files in os.walk(config.content_dir):
                for f in files:
                    src_f = Path(root) / f
                    if src_f.suffix.lower() in media_exts:
                        try:
                            rel_asset = src_f.relative_to(config.content_dir)
                            target_asset = out_dir / rel_asset
                            target_asset.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_f, target_asset)
                        except ValueError:
                            pass

        # 6. Compile each page
        for page in config.pages:
            self._compile_page(
                page=page,
                config=config,
                out_dir=out_dir,
                extra_css_content=extra_css_content,
                standalone=standalone,
                live_reload=live_reload,
            )

        # 7. Copy any referenced scripts detected during compilation (e.g. ::: plot)
        for script_path in self.compiler.watched_scripts:
            if script_path.exists() and script_path.is_file():
                try:
                    rel_script = script_path.relative_to(config.root_dir)
                    target_script = out_dir / rel_script
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(script_path, target_script)
                except ValueError:
                    pass

        return out_dir

    def _compile_page(
        self,
        page: PageMeta,
        config: SiteConfig,
        out_dir: Path,
        extra_css_content: str,
        standalone: bool,
        live_reload: bool,
    ) -> Path:
        """Compile a single page into the destination directory."""
        # Calculate root_path relative prefix (e.g. "", "../", "../../")
        rel_parts = Path(page.rel_html_path).parent.parts
        root_path = ("../" * len(rel_parts)) if (rel_parts and rel_parts != (".",)) else ""

        # Prepare adjusted breadcrumbs
        adjusted_breadcrumbs: list[dict[str, str | None]] = []
        for crumb in page.breadcrumbs:
            crumb_url = crumb.get("url")
            if crumb_url:
                adj_url = f"{root_path}{crumb_url}"
            else:
                adj_url = None
            adjusted_breadcrumbs.append({
                "title": str(crumb["title"]),
                "url": adj_url,
            })

        # Prepare adjusted prev and next page links
        adj_prev = None
        if page.prev_page:
            adj_prev = {
                "title": page.prev_page["title"],
                "url": f"{root_path}{page.prev_page['url']}",
            }

        adj_next = None
        if page.next_page:
            adj_next = {
                "title": page.next_page["title"],
                "url": f"{root_path}{page.next_page['url']}",
            }

        # Sibling CSS
        sibling_css = None
        if page.sibling_css_path and page.sibling_css_path.exists():
            sibling_css = page.sibling_css_path.read_text(encoding="utf-8")
            self.compiler.register_watched_script(page.sibling_css_path)

        static_prefix = f"{root_path}static" if not standalone else "/static"

        extra_ctx: dict[str, Any] = {
            "site_name": config.site_name,
            "brand": config.brand,
            "brand_icon": config.brand_icon,
            "snowpack_pdf": config.snowpack_pdf,
            "root_path": root_path,
            "breadcrumbs": adjusted_breadcrumbs,
            "prev_page": adj_prev,
            "next_page": adj_next,
            "extra_css_content": extra_css_content,
            "sibling_css": sibling_css,
            "static_prefix": static_prefix,
        }

        dest_html = out_dir / page.rel_html_path
        dest_html.parent.mkdir(parents=True, exist_ok=True)

        return self.compiler.compile_file(
            input_path=page.src_path,
            output_path=dest_html,
            template_name=config.template,
            standalone=standalone,
            live_reload=live_reload,
            extra_context=extra_ctx,
            rewrite_md_links=True,
        )
