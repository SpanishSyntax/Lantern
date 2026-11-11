# Getting Started

Lantern compiles markdown documents enriched with interactive widgets into standalone HTML applications.

---

## Installation

### Nix Flake (Recommended)

Lantern is packaged natively as a hermetic Nix Flake:

```bash
# Run lantern commands directly without installation
nix run github:SpanishSyntax/Lantern -- new my-explainer

# Enter an interactive dev shell
nix shell github:SpanishSyntax/Lantern
```

To add Lantern to your NixOS or Home Manager configuration:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    lantern = {
      url = "github:SpanishSyntax/Lantern";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, lantern, ... }: {
    homeConfigurations."usurper" = home-manager.lib.homeManagerConfiguration {
      modules = [
        lantern.homeManagerModules.default
        {
          programs.lantern.enable = true;
        }
      ];
    };
  };
}
```

### Python Package (pip / uv)

Lantern is standard PEP 517/621 compliant:

```bash
# Install with uv
uv tool install git+https://github.com/SpanishSyntax/Lantern.git

# Install with pip
pip install git+https://github.com/SpanishSyntax/Lantern.git
```

---

## Quick Start

### 1. Scaffold a New Project

Create a starter interactive explainer or simulation dashboard:

```bash
lantern new optimization-lab --template explainer
cd optimization-lab
```

This generates `explainer.md` containing interactive sliders, layout grids, and a linked Python plot script.

### 2. Live Server Development

Launch the live development server with browser auto-reloading:

```bash
lantern serve explainer.md
```

The server binds to `http://127.0.0.1:8080` (or the next available port). Any edits to `explainer.md` or any referenced Python plot scripts instantly refresh connected browser tabs via Server-Sent Events (SSE).

### 3. Build Standalone Production HTML

To generate a single, zero-dependency HTML file suitable for emailing or hosting:

```bash
lantern build explainer.md -o dist/ --standalone
```

The output in `dist/explainer.html` contains inlined CSS, KaTeX font definitions, and JavaScript widget code.

---

## Scaffolding Templates

Lantern provides three built-in templates:

| Template Name | Flag | Intended Workflow |
| :--- | :--- | :--- |
| `explainer` | `--template explainer` (default) | Pedagogical interactive article with ScrollSpy dot rail, stepper, and live math |
| `dashboard` | `--template dashboard` | Status metrics grid, responsive control cards, and multi-chart telemetry layouts |
| `optimization` | `--template optimization` | Numerical algorithm lab with 2D landscape walker and penalty constraint sweeps |
