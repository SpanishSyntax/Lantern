# Lantern: Multi-Page Explorable Engine Architecture Mission

> **Target Repository:** `~/Icebergs/Lantern` (`/home/usurper/Icebergs/Lantern`)  
> **Mission Lead:** Frost Architecture Team  
> **Objective:** Upgrade Lantern from a single-document scientific compiler into a first-class **Multi-Page Scientific Explorable Engine**, adopting the proven ergonomics of MkDocs while preserving Lantern's native computational superpowers.

---

## 1. Executive Summary & Problem Statement

### 1.1 The Problem
Currently, Lantern (`lantern build <file.md>`, `lantern serve <file.md>`) is architected strictly around a **single target file**. When building comprehensive technical portals (such as a multi-chapter university course, a multi-paper research series, or an interactive algorithm hub):
1. **The Monolithic Markdown Trap:** Authors are forced to cram dozens of topics, 3D WebGL plots, and interactive quizzes into a single 200+ KB `.md` file with client-side SPA hash-routing hacks (`#hub`, `#algo-gd`).
2. **Embedded CSS Pollution:** Authors inline large `<style>` blocks directly into `.md` files because Lantern lacks a formal mechanism for site-wide stylesheets, sibling CSS discovery, or scoped CSS overrides.
3. **Single-Target Dev Server:** `lantern serve` only accepts a single file and cannot watch a multi-page directory tree or serve clean hierarchical URLs (`/`, `/algos/gd.html`, `/quizzes/gd.html`).

### 1.2 The Vision
Lantern should not become a bloated generic CMS. Instead, it should adopt the **5 gold-standard ergonomics of MkDocs**, combined seamlessly with **Lantern's native computational superpowers**:

| What We Adopt from MkDocs | What Lantern Keeps (Its Superpowers) |
| :--- | :--- |
| **Directory-as-Routing:** Folder hierarchy defines clean URLs (`/`, `/algos/gd.html`). | **Native Python Plot Execution:** `::: plot script.py` runs live via Barograph. |
| **Site Manifest (`site.yaml`):** Navigation tree, site title, companion PDF. | **Bret Victor Explorable Directives:** `::: slider`, `::: switch`, `::: player`. |
| **Global Navigation Shell:** Auto-generated breadcrumbs, brand top-bar, and prev/next links. | **Zero-Dependency `--standalone`:** Inlines KaTeX, Plotly WebGL, and CSS into single files. |
| **Zero CSS in Markdown:** Sibling CSS auto-discovery and global stylesheets. | **Linear / Apple / Glassmorphic Dark UI:** Native obsidian aesthetics, not standard Material. |
| **Live Multi-Page Dev Server:** Watches all markdown, python plots, and stylesheets. | **In-Memory SSE Synchronization:** Zero Node/NPM dependencies, pure Python 3.13. |

---

## 2. Target Directory Hierarchy & UX

When an author creates a project, it should look clean, modular, and human-readable:

```text
my-scientific-project/
├── site.yaml                       # Optional site manifest & navigation tree
├── styles/
│   └── site.css                    # Optional global CSS overrides
├── plots/                          # Python simulation & manifold scripts
│   ├── plot_rosenbrock_3d.py
│   └── plot_simplex_polytope.py
└── content/                        # Markdown source hierarchy
    ├── index.md                    # Landing page (serves as '/')
    ├── algos/
    │   ├── gd.md                   # Clean 80-line guide for Gradient Descent
    │   ├── gd.css                  # Sibling CSS automatically scoped to gd.md!
    │   └── newton.md               # Clean guide for Newton-Raphson
    ├── quizzes/
    │   ├── gd.md                   # Dedicated Gradient Descent quiz
    │   └── newton.md
    └── exam/
        └── master.md               # Course-wide master exam
```

### Build & Serve Commands
```bash
# Compile entire multi-page site into dist/
lantern build content/ -o dist/
# or targeting the manifest:
lantern build site.yaml -o dist/

# Live dev server watching all markdown, python scripts, and sibling CSS:
lantern serve content/ -p 8080
# or:
lantern serve site.yaml -p 8080
```

---

## 3. Core Architectural Specifications

### 3.1 Site Manifest (`site.yaml`) Specification
Create a lightweight YAML parser (`src/lantern/config.py`):

```yaml
site_name: "SC42056 Optimization for Systems and Control"
brand: "SC42056 Hub"
brand_icon: "🏮"
template: "explainer" # default layout
snowpack_pdf: "report.pdf" # links companion PDF in top-nav

# Global stylesheets applied to every page
extra_css:
  - "styles/site.css"

# Global scripts
extra_javascript: []

# Hierarchical Navigation Tree
nav:
  - Home: "content/index.md"
  - Unconstrained Optimization:
      - "Gradient Descent": "content/algos/gd.md"
      - "Newton-Raphson": "content/algos/newton.md"
  - Exam Quizzes:
      - "Gradient Descent Quiz": "content/quizzes/gd.md"
      - "Master Exam Arena": "content/exam/master.md"
```

*Auto-Inference Fallback:* If `site.yaml` does not exist, Lantern must automatically infer the nav tree by walking the `content/` directory recursively, sorting files alphabetically or by numeric prefix (`01_intro.md`).

---

### 3.2 Sibling CSS Auto-Discovery & Scoped Overrides
Authors should never have to write `<style>` in Markdown.
In `LanternCompiler.compile()`:
1. When compiling `path/to/page.md`, check if `path/to/page.css` exists.
2. If found, automatically read `page.css` and inject it into the template's `head_extra` block (inlined for `--standalone`, or linked as `<link rel="stylesheet" href="...">` for multi-page static output).
3. Support frontmatter CSS overrides:
   ```yaml
   ---
   title: Newton Method
   css:
     - ../shared_cards.css
     - ./custom_matrix.css
   ---
   ```

---

### 3.3 Global Shell & Automatic Breadcrumbs
Enhance `src/lantern/templates/base.html.j2`:
1. **Top Navigation Bar:**
   - Brand icon & site title linked to `/index.html`.
   - **Breadcrumb Trail:** Rendered dynamically from the nav tree (e.g. `Home / Unconstrained / Gradient Descent`).
   - Action buttons: "📖 Companion PDF Reader" (if `snowpack_pdf` is defined), search toggle.
2. **Page Footer Navigation:**
   - Automatically calculate `prev_page` and `next_page` from the nav manifest.
   - Render clean pagination links:
     `← Previous: Nelder-Mead` | `Next: Newton-Raphson →`

---

### 3.4 Multi-Page Compiler Engine (`src/lantern/site.py`)
Implement a dedicated `SiteCompiler`:
1. Parse `site.yaml` or scan the root content directory.
2. Build the navigation graph (calculating URLs, breadcrumbs, previous/next links for each page).
3. For each markdown document:
   - Calculate relative output path (`content/algos/gd.md` $\to$ `dist/algos/gd.html`).
   - Execute `LanternCompiler.compile()` with `extra_context` containing:
     - `site_name`, `brand`, `snowpack_pdf`.
     - `breadcrumbs`: List of `{"title": str, "url": str}`.
     - `prev_page`: `{"title": str, "url": str}` or `None`.
     - `next_page`: `{"title": str, "url": str}` or `None`.
     - `sibling_css`: Content of sibling `.css` file if present.
     - `root_path`: Relative prefix to site root (`../`, `../../`, or empty).
   - Resolve relative hyperlink targets (`[Next](newton.md)` $\to$ `[Next](newton.html)`).
4. Copy/export all referenced assets, static files, and plots.

---

### 3.5 Upgraded Dev Server (`src/lantern/server.py`)
Upgrade `LanternDevServer` to handle both single-file and directory targets:
1. **Dynamic Multi-Route Handler:**
   - Serve `/` $\to$ `index.html`.
   - Serve `/algos/gd` or `/algos/gd.html` dynamically by compiling `content/algos/gd.md` on demand (with caching).
   - Serve static assets (`/static/*`, `/styles/*`, `/plots/*`).
2. **Full-Tree File Watcher:**
   - Use `watchdog` to monitor the entire `content/` folder, all sibling `.css` files, referenced Python plot scripts in `plots/`, and `site.yaml`.
   - On file change, trigger the existing SSE client queue (`/_lantern/events`) to hot-reload connected browser tabs.

---

## 4. Implementation Checklist for the Developer Agent

- [ ] **Step 1: Manifest & Config Parser (`src/lantern/config.py`)**
  - Implement `SiteConfig.load(path: Path | None)` reading YAML with PyYAML (or fallback regex/json if PyYAML is not in store).
  - Implement automatic nav tree inference when `site.yaml` is absent.
- [ ] **Step 2: Sibling CSS Discovery (`src/lantern/compiler.py`)**
  - In `LanternCompiler.compile_file(path: Path)`, detect `path.with_suffix('.css')`.
  - Pass sibling CSS content into Jinja context as `sibling_css`.
- [ ] **Step 3: Multi-Page Site Compiler (`src/lantern/site.py`)**
  - Implement `LanternSiteBuilder.build(config: SiteConfig, out_dir: Path, standalone: bool)`.
  - Calculate relative paths, nav breadcrumbs, prev/next links.
  - Re-write `.md` links to `.html` in compiled prose.
- [ ] **Step 4: Template Upgrades (`src/lantern/templates/base.html.j2` & `explainer.html.j2`)**
  - Add breadcrumbs block to header.
  - Add previous/next article footer buttons.
  - Add `{% if sibling_css %}<style>{{ sibling_css | safe }}</style>{% endif %}` to `<head>`.
- [ ] **Step 5: CLI Integration (`src/lantern/cli.py`)**
  - In `cmd_build`: Check if target is a directory or `site.yaml`; dispatch to `LanternSiteBuilder`.
  - In `cmd_serve`: If target is directory or `site.yaml`, spin up `LanternSiteDevServer`.
- [ ] **Step 6: Test Suite (`tests/test_multipage.py`)**
  - Test building a multi-page sample with sibling CSS and nested subdirectories.
  - Verify zero unparsed directives, zero broken links, and valid KaTeX/Plotly output.

---

## 5. Acceptance Test Case (TU Delft SC42056 Lab)

When complete, the following directory structure must compile and run flawlessly:

```bash
cd "/home/usurper/Workspace/TUDelft/SC42056 Optimization"
lantern build site.yaml -o dist/
```

- `dist/index.html` loads the Master Algorithm Grid with zero inline CSS.
- Clicking any card navigates to `/algos/gd.html` (instant browser navigation, zero hash hacks).
- `/algos/gd.html` executes `plots/plot_rosenbrock_3d.py` via Barograph and shows the 3D surface.
- Sibling `gd.css` is applied without affecting any other page.
- Breadcrumb displays `SC42056 Hub / Unconstrained / Gradient Descent`.
- Next button leads directly to `Newton-Raphson`.
- `lantern serve site.yaml -p 8080` serves the entire site with SSE hot-reload on any `.md` or `.py` plot edit.
