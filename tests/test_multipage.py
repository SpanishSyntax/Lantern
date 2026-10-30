"""Comprehensive tests for Lantern Multi-Page Scientific Explorable Engine."""

import threading
import time
import urllib.request
from pathlib import Path

import pytest
from lantern.cli import main
from lantern.compiler import LanternCompiler
from lantern.config import SiteConfig
from lantern.server import LanternDevServer
from lantern.site import LanternSiteBuilder


def test_site_config_from_yaml(tmp_path):
    site_yaml = tmp_path / "site.yaml"
    site_yaml.write_text(
        """site_name: "Optimization Portal"
brand: "SC42056 Hub"
brand_icon: "🏮"
template: "explainer"
snowpack_pdf: "report.pdf"
extra_css:
  - "styles/site.css"
nav:
  - Home: "content/index.md"
  - Unconstrained:
      - "Gradient Descent": "content/algos/gd.md"
      - "Newton-Raphson": "content/algos/newton.md"
""",
        encoding="utf-8",
    )

    content_dir = tmp_path / "content"
    algos_dir = content_dir / "algos"
    algos_dir.mkdir(parents=True)

    (content_dir / "index.md").write_text("# Home Portal\nWelcome.", encoding="utf-8")
    (algos_dir / "gd.md").write_text("# Gradient Descent\nProse here.", encoding="utf-8")
    (algos_dir / "newton.md").write_text("# Newton Method\nProse here.", encoding="utf-8")
    (algos_dir / "gd.css").write_text(".gd-highlight { color: cyan; }", encoding="utf-8")

    config = SiteConfig.load(site_yaml)

    assert config.site_name == "Optimization Portal"
    assert config.brand == "SC42056 Hub"
    assert config.brand_icon == "🏮"
    assert len(config.pages) == 3

    # Check Page 0 (Home)
    p0 = config.pages[0]
    assert p0.title == "Home"
    assert p0.rel_html_path == "index.html"
    assert p0.prev_page is None
    assert p0.next_page["title"] == "Gradient Descent"
    assert p0.next_page["url"] == "algos/gd.html"

    # Check Page 1 (GD)
    p1 = config.pages[1]
    assert p1.title == "Gradient Descent"
    assert p1.rel_html_path == "algos/gd.html"
    assert p1.prev_page["title"] == "Home"
    assert p1.prev_page["url"] == "index.html"
    assert p1.next_page["title"] == "Newton-Raphson"
    assert p1.next_page["url"] == "algos/newton.html"
    assert p1.sibling_css_path == algos_dir / "gd.css"

    # Breadcrumb check: SC42056 Hub / Unconstrained / Gradient Descent
    crumb_titles = [c["title"] for c in p1.breadcrumbs]
    assert crumb_titles == ["SC42056 Hub", "Unconstrained", "Gradient Descent"]


def test_site_config_auto_inference(tmp_path):
    content_dir = tmp_path / "content"
    algos_dir = content_dir / "algos"
    quizzes_dir = content_dir / "quizzes"
    algos_dir.mkdir(parents=True)
    quizzes_dir.mkdir(parents=True)

    (content_dir / "index.md").write_text("# Master Index\nContent.", encoding="utf-8")
    (algos_dir / "01_gd.md").write_text(
        "---\ntitle: \"Gradient Descent\"\n---\n# GD", encoding="utf-8"
    )
    (algos_dir / "02_newton.md").write_text("# Newton-Raphson Method", encoding="utf-8")
    (quizzes_dir / "quiz.md").write_text("# Master Quiz", encoding="utf-8")

    # Load from directory without site.yaml
    config = SiteConfig.load(tmp_path)

    assert len(config.pages) == 4
    assert config.pages[0].rel_html_path == "index.html"
    assert config.pages[0].title == "Master Index"

    # Ordering check: 01_gd before 02_newton
    page_urls = [p.rel_html_path for p in config.pages]
    assert page_urls == [
        "index.html",
        "algos/01_gd.html",
        "algos/02_newton.html",
        "quizzes/quiz.html",
    ]


def test_sibling_css_and_frontmatter_css(tmp_path):
    compiler = LanternCompiler()

    md_path = tmp_path / "article.md"
    css_path = tmp_path / "article.css"
    extra_style = tmp_path / "shared.css"

    extra_style.write_text(".shared-badge { font-weight: bold; }", encoding="utf-8")
    css_path.write_text(".article-card { border: 1px solid green; }", encoding="utf-8")
    md_path.write_text(
        """---
title: "Article with Sibling & Scoped CSS"
css:
  - shared.css
---
# Article Body
Content here.
""",
        encoding="utf-8",
    )

    out_file = compiler.compile_file(md_path)
    content = out_file.read_text(encoding="utf-8")

    # Verify both sibling and frontmatter CSS are injected
    assert "article-card" in content
    assert "shared-badge" in content
    assert "lantern-sibling-css" in content


def test_multi_page_site_builder(tmp_path):
    site_dir = tmp_path / "my_site"
    content_dir = site_dir / "content"
    algos_dir = content_dir / "algos"
    styles_dir = site_dir / "styles"
    algos_dir.mkdir(parents=True)
    styles_dir.mkdir(parents=True)

    (styles_dir / "site.css").write_text(":root { --brand-color: #38bdf8; }", encoding="utf-8")
    (site_dir / "report.pdf").write_text("%PDF-1.4 mock pdf", encoding="utf-8")

    (site_dir / "site.yaml").write_text(
        """site_name: "SC42056 Optimization"
brand: "SC42056 Hub"
brand_icon: "🏮"
snowpack_pdf: "report.pdf"
extra_css:
  - "styles/site.css"
nav:
  - Home: "content/index.md"
  - Unconstrained:
      - "Gradient Descent": "content/algos/gd.md"
      - "Newton-Raphson": "content/algos/newton.md"
""",
        encoding="utf-8",
    )

    (content_dir / "index.md").write_text(
        """# Optimization Hub
Navigate to [Gradient Descent](algos/gd.md).
""",
        encoding="utf-8",
    )

    (algos_dir / "gd.css").write_text(".gd-specific { color: red; }", encoding="utf-8")
    (algos_dir / "gd.md").write_text(
        """# Gradient Descent
Math: $x_{k+1} = x_k - \\alpha \\nabla f(x_k)$.
See next: [Newton-Raphson](newton.md).
""",
        encoding="utf-8",
    )

    (algos_dir / "newton.md").write_text(
        """# Newton-Raphson
Second order curvature.
""",
        encoding="utf-8",
    )

    dist_dir = site_dir / "dist"
    builder = LanternSiteBuilder()
    builder.build(target=site_dir / "site.yaml", output_dir=dist_dir)

    # 1. Output files exist
    assert (dist_dir / "index.html").exists()
    assert (dist_dir / "algos" / "gd.html").exists()
    assert (dist_dir / "algos" / "newton.html").exists()
    assert (dist_dir / "static" / "lantern.css").exists()
    assert (dist_dir / "styles" / "site.css").exists()
    assert (dist_dir / "report.pdf").exists()

    # 2. Check index.html
    index_html = (dist_dir / "index.html").read_text(encoding="utf-8")
    assert "href=\"algos/gd.html\"" in index_html  # rewritten .md -> .html
    assert "SC42056 Hub" in index_html
    assert "lantern-extra-css" in index_html

    # 3. Check algos/gd.html
    gd_html = (dist_dir / "algos" / "gd.html").read_text(encoding="utf-8")
    # Sibling CSS scoped to gd.html
    assert "gd-specific" in gd_html
    assert "lantern-sibling-css" in gd_html
    # Rewritten links
    assert "href=\"newton.html\"" in gd_html
    # KaTeX math preserved
    assert "$x_{k+1} = x_k - \\alpha \\nabla f(x_k)$" in gd_html
    # Breadcrumbs
    assert "SC42056 Hub" in gd_html
    assert "Unconstrained" in gd_html
    assert "Gradient Descent" in gd_html
    # Pagination: prev to Home, next to Newton
    assert "lantern-page-nav-prev" in gd_html
    assert "lantern-page-nav-next" in gd_html
    assert "../index.html" in gd_html
    assert "newton.html" in gd_html

    # 4. Check newton.html has no gd.css
    newton_html = (dist_dir / "algos" / "newton.html").read_text(encoding="utf-8")
    assert "gd-specific" not in newton_html


def test_dev_server_multipage_routes(tmp_path):
    site_dir = tmp_path / "dev_site"
    content_dir = site_dir / "content"
    algos_dir = content_dir / "algos"
    algos_dir.mkdir(parents=True)

    (site_dir / "site.yaml").write_text(
        """site_name: "Test Dev Site"
brand: "Dev Hub"
nav:
  - Home: "content/index.md"
  - Algos:
      - "Gradient Descent": "content/algos/gd.md"
""",
        encoding="utf-8",
    )

    (content_dir / "index.md").write_text("# Home Page\nWelcome to dev server.", encoding="utf-8")
    (algos_dir / "gd.css").write_text(".gd-theme { color: yellow; }", encoding="utf-8")
    (algos_dir / "gd.md").write_text("# GD Page\nLive dev content.", encoding="utf-8")

    server = LanternDevServer(
        target_file=site_dir / "site.yaml",
        port=9885,
        host="127.0.0.1",
    )

    # Start server in background thread
    server_thread = threading.Thread(target=server.start, kwargs={"open_browser": False}, daemon=True)
    server_thread.start()

    # Wait until httpd is bound
    for _ in range(50):
        if server.httpd is not None:
            break
        time.sleep(0.05)

    base_url = f"http://{server.host}:{server.port}"

    try:
        # Route 1: /
        with urllib.request.urlopen(f"{base_url}/", timeout=3) as res:
            assert res.status == 200
            body = res.read().decode("utf-8")
            assert "Welcome to dev server." in body
            assert "Dev Hub" in body

        # Route 2: /algos/gd.html
        with urllib.request.urlopen(f"{base_url}/algos/gd.html", timeout=3) as res:
            assert res.status == 200
            body = res.read().decode("utf-8")
            assert "Live dev content." in body
            assert "gd-theme" in body

        # Route 3: /static/lantern.css
        with urllib.request.urlopen(f"{base_url}/static/lantern.css", timeout=3) as res:
            assert res.status == 200
            assert "css" in res.headers.get("Content-Type", "")

    finally:
        server.shutdown()


def test_cli_multipage_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    site_dir = tmp_path / "cli_site"
    content_dir = site_dir / "content"
    content_dir.mkdir(parents=True)

    (site_dir / "site.yaml").write_text(
        """site_name: "CLI Site Test"
brand: "CLI Brand"
nav:
  - Home: "content/index.md"
""",
        encoding="utf-8",
    )
    (content_dir / "index.md").write_text("# CLI Index Page", encoding="utf-8")

    dist_dir = site_dir / "out"
    ret = main(["build", str(site_dir / "site.yaml"), "-o", str(dist_dir)])
    assert ret == 0
    assert (dist_dir / "index.html").exists()
    content = (dist_dir / "index.html").read_text(encoding="utf-8")
    assert "CLI Index Page" in content
    assert "CLI Brand" in content
