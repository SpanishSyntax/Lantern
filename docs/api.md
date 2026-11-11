# Configuration & API Reference

This reference covers project configuration, the reactive DOM event specification, and the Python programmatic API.

---

## Site Configuration

A project can define optional site-wide configuration in `lantern.yaml` or directly in Markdown YAML frontmatter:

```yaml
title: "Numerical Optimization Lab"
description: "Interactive exploration of first and second-order descent methods"
author: "Alex Rivera"
template: "explainer"
theme:
  accent: "#F59E0B"
  background: "#0F172A"
  surface: "#1E293B"
  text: "#CBD5E1"
features:
  scrollspy: true
  katex: true
  plotly: true
```

---

## DOM Event Specification

Lantern components communicate via the standard DOM event bus. Any custom widget or script can subscribe or emit events using `window.addEventListener`:

### Listening to Parameter Changes

```javascript
window.addEventListener('lantern:input', (event) => {
  const { id, value } = event.detail;
  console.log(`Parameter changed: ${id} = ${value}`);
  
  if (id === 'damping_ratio') {
    updateSimulationDynamics(parseFloat(value));
  }
});
```

### Emitting Parameter Changes

```javascript
window.dispatchEvent(new CustomEvent('lantern:input', {
  detail: {
    id: 'damping_ratio',
    value: 0.85
  }
}));
```

---

## Python API Reference

Lantern provides a Python library interface for compiling documents and managing dev servers programmatically:

```python
from pathlib import Path
from lantern.compiler import LanternCompiler
from lantern.config import SiteConfig
from lantern.server import LanternDevServer
from lantern.scaffold import create_project
```

### `LanternCompiler`

The primary compilation engine.

```python
class LanternCompiler:
    def __init__(self, config: SiteConfig | None = None) -> None:
        """Initializes the compiler with optional site configuration."""
        
    def compile_file(
        self,
        source_path: Path,
        output_path: Path | None = None,
        standalone: bool = False,
        template_name: str = "explainer",
    ) -> Path:
        """Compiles a Markdown file into an HTML artifact.
        
        Args:
            source_path: Path to the input .md file.
            output_path: Target path for the generated HTML.
            standalone: Inlines all CSS, JS, and math assets when True.
            template_name: Template identifier ('explainer', 'dashboard', 'optimization').
            
        Returns:
            Path: Path to the generated HTML file.
        """
```

### `LanternDevServer`

Programmatic live-reloading dev server.

```python
class LanternDevServer:
    def __init__(
        self,
        target_file: Path,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        """Initializes the SSE auto-reloading server."""
        
    def start(self, open_browser: bool = False) -> None:
        """Runs the server on the designated host and port."""
```

### `create_project`

Scaffolds a new project directory.

```python
def create_project(
    project_dir: Path,
    template_name: str = "explainer",
) -> Path:
    """Scaffolds starter markdown files and plot scripts."""
```

---

## Nix Integration

### Flake Configuration

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    lantern = {
      url = "github:SpanishSyntax/Lantern";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
}
```

### Home Manager Module

```nix
{
  programs.lantern = {
    enable = true;
  };
}
```
