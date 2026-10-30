"""Site configuration and navigation manifest parser for Lantern."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Lightweight fallback YAML parser for environments without PyYAML."""
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()

            if not v:
                # Nested list or dictionary
                sub_lines: list[tuple[int, str]] = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith("#"):
                        i += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    if next_indent <= indent:
                        break
                    sub_lines.append((next_indent, next_line))
                    i += 1

                # Detect if list or dict
                if sub_lines and sub_lines[0][1].strip().startswith("-"):
                    result[k] = _parse_yaml_list(sub_lines)
                else:
                    result[k] = _parse_yaml_dict(sub_lines)
                continue
            else:
                v_clean = v.strip("\"'")
                if v_clean.lower() == "true":
                    result[k] = True
                elif v_clean.lower() == "false":
                    result[k] = False
                elif v_clean.isdigit():
                    result[k] = int(v_clean)
                else:
                    result[k] = v_clean
        i += 1
    return result


def _parse_yaml_list(lines: list[tuple[int, str]]) -> list[Any]:
    items: list[Any] = []
    base_indent = lines[0][0] if lines else 0
    idx = 0
    while idx < len(lines):
        indent, line = lines[idx]
        stripped = line.strip()
        if stripped.startswith("- "):
            content = stripped[2:].strip()
            if ":" in content:
                # Dict item inside list, e.g. - Home: "content/index.md"
                # or - Section:
                #       - Page: "..."
                key, val = content.split(":", 1)
                key = key.strip().strip("\"'")
                val = val.strip().strip("\"'")
                if val:
                    items.append({key: val})
                    idx += 1
                else:
                    # Collect children lines with deeper indentation
                    child_lines: list[tuple[int, str]] = []
                    idx += 1
                    while idx < len(lines):
                        c_indent, c_line = lines[idx]
                        if c_indent <= indent:
                            break
                        child_lines.append((c_indent, c_line))
                        idx += 1
                    if child_lines and child_lines[0][1].strip().startswith("-"):
                        items.append({key: _parse_yaml_list(child_lines)})
                    else:
                        items.append({key: _parse_yaml_dict(child_lines)})
            else:
                items.append(content.strip("\"'"))
                idx += 1
        else:
            idx += 1
    return items


def _parse_yaml_dict(lines: list[tuple[int, str]]) -> dict[str, Any]:
    res: dict[str, Any] = {}
    base_indent = lines[0][0] if lines else 0
    for indent, line in lines:
        if indent == base_indent:
            stripped = line.strip()
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                res[k.strip().strip("\"'")] = v.strip().strip("\"'")
    return res


def parse_yaml_safely(text: str) -> dict[str, Any]:
    """Parse YAML string using PyYAML if available, with resilient fallback."""
    try:
        import yaml

        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
        return _parse_simple_yaml(text)
    except Exception:
        return _parse_simple_yaml(text)


def extract_frontmatter_and_title(file_path: Path) -> tuple[dict[str, Any], str]:
    """Extract frontmatter and best document title from a markdown file."""
    if not file_path.exists() or not file_path.is_file():
        return {}, file_path.stem.title()

    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return {}, file_path.stem.title()

    fm: dict[str, Any] = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parse_yaml_safely(parts[1])
            content = parts[2]

    # Frontmatter title takes precedence
    if "title" in fm and fm["title"]:
        return fm, str(fm["title"]).strip()

    # Search for first H1
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return fm, line[2:].strip()

    # Default to formatted filename
    stem = file_path.stem
    if stem.lower() in ("index", "readme"):
        title = "Home"
    else:
        title = stem.replace("_", " ").replace("-", " ").title()

    return fm, title


@dataclass
class PageMeta:
    """Metadata and navigation pointers for a single page within a multi-page site."""

    title: str
    src_path: Path
    rel_path: str
    rel_html_path: str
    breadcrumbs: list[dict[str, str | None]] = field(default_factory=list)
    prev_page: dict[str, str] | None = None
    next_page: dict[str, str] | None = None
    sibling_css_path: Path | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass
class SiteConfig:
    """Configuration manifest for a multi-page Lantern explorable site."""

    site_name: str = "Lantern Site"
    brand: str = "Lantern"
    brand_icon: str = "🏮"
    template: str = "explainer"
    snowpack_pdf: str | None = None
    extra_css: list[str] = field(default_factory=list)
    extra_javascript: list[str] = field(default_factory=list)
    nav: list[Any] = field(default_factory=list)
    root_dir: Path = field(default_factory=Path.cwd)
    content_dir: Path = field(default_factory=Path.cwd)
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "dist")
    pages: list[PageMeta] = field(default_factory=list)

    @classmethod
    def load(
        cls,
        target: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> SiteConfig:
        """Load site configuration from site.yaml or infer from content directory."""
        target_path = Path(target).resolve() if target else Path.cwd().resolve()
        config_data: dict[str, Any] = {}
        manifest_file: Path | None = None

        if target_path.is_file() and target_path.name in ("site.yaml", "site.yml"):
            manifest_file = target_path
            root_dir = target_path.parent
        elif target_path.is_dir():
            if (target_path / "site.yaml").exists():
                manifest_file = target_path / "site.yaml"
                root_dir = target_path
            elif (target_path / "site.yml").exists():
                manifest_file = target_path / "site.yml"
                root_dir = target_path
            elif target_path.name == "content" and (target_path.parent / "site.yaml").exists():
                manifest_file = target_path.parent / "site.yaml"
                root_dir = target_path.parent
            else:
                root_dir = target_path.parent if target_path.name == "content" else target_path
        else:
            root_dir = target_path.parent

        if manifest_file and manifest_file.exists():
            text = manifest_file.read_text(encoding="utf-8")
            config_data = parse_yaml_safely(text)

        # Resolve content directory
        if "content_dir" in config_data:
            content_dir = (root_dir / str(config_data["content_dir"])).resolve()
        elif (root_dir / "content").is_dir():
            content_dir = (root_dir / "content").resolve()
        elif target_path.is_dir() and target_path.name == "content":
            content_dir = target_path
        else:
            content_dir = root_dir

        # Determine output directory
        if output_dir is not None:
            out_p = Path(output_dir).resolve()
        elif "output_dir" in config_data:
            out_p = (root_dir / str(config_data["output_dir"])).resolve()
        else:
            out_p = (root_dir / "dist").resolve()

        site_name = str(config_data.get("site_name") or root_dir.name.replace("_", " ").title())
        brand = str(config_data.get("brand") or site_name)
        brand_icon = str(config_data.get("brand_icon") or "🏮")
        template = str(config_data.get("template") or "explainer")
        snowpack_pdf = config_data.get("snowpack_pdf")
        extra_css = list(config_data.get("extra_css") or [])
        extra_javascript = list(config_data.get("extra_javascript") or [])
        raw_nav = list(config_data.get("nav") or [])

        instance = cls(
            site_name=site_name,
            brand=brand,
            brand_icon=brand_icon,
            template=template,
            snowpack_pdf=snowpack_pdf,
            extra_css=extra_css,
            extra_javascript=extra_javascript,
            nav=raw_nav,
            root_dir=root_dir,
            content_dir=content_dir,
            output_dir=out_p,
        )

        instance._build_pages()
        return instance

    def _resolve_file(self, path_str: str) -> Path | None:
        """Resolve a nav item path string to an existing Markdown file."""
        clean_path = path_str.strip()
        candidates = [
            (self.root_dir / clean_path).resolve(),
            (self.content_dir / clean_path).resolve(),
        ]
        if clean_path.startswith("content/"):
            candidates.append((self.root_dir / clean_path).resolve())
            candidates.append((self.content_dir / clean_path[len("content/") :]).resolve())

        for c in candidates:
            if c.exists() and c.is_file():
                return c
        return None

    def _calculate_rel_html_path(self, file_path: Path) -> str:
        """Calculate relative output HTML path within dist/."""
        try:
            rel = file_path.relative_to(self.content_dir)
        except ValueError:
            try:
                rel = file_path.relative_to(self.root_dir)
            except ValueError:
                rel = Path(file_path.name)

        return rel.with_suffix(".html").as_posix()

    def _build_pages(self) -> None:
        """Construct the ordered list of PageMeta objects with breadcrumbs and prev/next links."""
        pages: list[PageMeta] = []

        if self.nav:
            # Parse explicitly declared navigation tree
            pages = self._parse_nav_tree(self.nav, section_stack=[])
        else:
            # Auto-infer navigation tree by crawling content directory
            pages = self._infer_nav_tree()

        # Connect previous and next page links
        for i, page in enumerate(pages):
            if i > 0:
                page.prev_page = {
                    "title": pages[i - 1].title,
                    "url": pages[i - 1].rel_html_path,
                }
            else:
                page.prev_page = None

            if i < len(pages) - 1:
                page.next_page = {
                    "title": pages[i + 1].title,
                    "url": pages[i + 1].rel_html_path,
                }
            else:
                page.next_page = None

            # Detect sibling CSS
            sibling = page.src_path.with_suffix(".css")
            if sibling.exists() and sibling.is_file():
                page.sibling_css_path = sibling

        self.pages = pages

    def _parse_nav_tree(
        self,
        nav_items: list[Any],
        section_stack: list[str],
    ) -> list[PageMeta]:
        """Recursively parse navigation tree list."""
        pages: list[PageMeta] = []

        for item in nav_items:
            if isinstance(item, str):
                resolved = self._resolve_file(item)
                if resolved:
                    fm, title = extract_frontmatter_and_title(resolved)
                    rel_html = self._calculate_rel_html_path(resolved)
                    crumbs = self._make_breadcrumbs(section_stack, title, rel_html)
                    pages.append(
                        PageMeta(
                            title=title,
                            src_path=resolved,
                            rel_path=str(resolved.relative_to(self.root_dir)),
                            rel_html_path=rel_html,
                            breadcrumbs=crumbs,
                            frontmatter=fm,
                        )
                    )
            elif isinstance(item, dict):
                for key, val in item.items():
                    if isinstance(val, str):
                        resolved = self._resolve_file(val)
                        if resolved:
                            fm, auto_title = extract_frontmatter_and_title(resolved)
                            title = key.strip() if key else auto_title
                            rel_html = self._calculate_rel_html_path(resolved)
                            crumbs = self._make_breadcrumbs(section_stack, title, rel_html)
                            pages.append(
                                PageMeta(
                                    title=title,
                                    src_path=resolved,
                                    rel_path=str(resolved.relative_to(self.root_dir)),
                                    rel_html_path=rel_html,
                                    breadcrumbs=crumbs,
                                    frontmatter=fm,
                                )
                            )
                    elif isinstance(val, list):
                        new_stack = section_stack + [str(key).strip()]
                        pages.extend(self._parse_nav_tree(val, new_stack))

        return pages

    def _make_breadcrumbs(
        self,
        section_stack: list[str],
        page_title: str,
        rel_html_path: str,
    ) -> list[dict[str, str | None]]:
        """Construct breadcrumb trail matching 'SC42056 Hub / Unconstrained / Gradient Descent'."""
        crumbs: list[dict[str, str | None]] = []

        # Root brand / home crumb
        brand_name = self.brand or self.site_name
        crumbs.append({"title": brand_name, "url": "index.html"})

        # Intermediate sections
        for sec in section_stack:
            crumbs.append({"title": sec, "url": None})

        # Final page crumb (if not already index home)
        if rel_html_path != "index.html" or section_stack:
            crumbs.append({"title": page_title, "url": rel_html_path})

        return crumbs

    def _infer_nav_tree(self) -> list[PageMeta]:
        """Automatically crawl content directory hierarchy to build navigation."""
        pages: list[PageMeta] = []
        if not self.content_dir.exists():
            return pages

        ignore_dirs = {".git", ".direnv", "node_modules", "dist", "build", "__pycache__", "result"}

        # Find all markdown files
        all_mds: list[Path] = []
        for root, dirs, files in os.walk(self.content_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for f in files:
                if f.endswith(".md") and not f.startswith((".", "#")):
                    all_mds.append((Path(root) / f).resolve())

        # Sort files: index.md first, then numerically or alphabetically
        def file_sort_key(p: Path) -> tuple[int, int, str]:
            rel = p.relative_to(self.content_dir)
            depth = len(rel.parts)
            is_root_index = 0 if rel.as_posix() == "index.md" else 1

            # Extract numeric prefix if present (e.g. '01_intro.md' -> 1)
            stem = p.stem
            match = re.match(r"^(\d+)[_\-\s]", stem)
            num = int(match.group(1)) if match else 9999

            return (depth, is_root_index, str(rel))

        sorted_files = sorted(all_mds, key=file_sort_key)

        for f in sorted_files:
            rel = f.relative_to(self.content_dir)
            fm, title = extract_frontmatter_and_title(f)
            rel_html = rel.with_suffix(".html").as_posix()

            # Build section stack from directory parts
            section_stack = [
                part.replace("_", " ").replace("-", " ").title()
                for part in rel.parent.parts
                if part and part != "."
            ]

            crumbs = self._make_breadcrumbs(section_stack, title, rel_html)

            pages.append(
                PageMeta(
                    title=title,
                    src_path=f,
                    rel_path=str(f.relative_to(self.root_dir)),
                    rel_html_path=rel_html,
                    breadcrumbs=crumbs,
                    frontmatter=fm,
                )
            )

        return pages
