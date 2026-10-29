"""Tests for Lantern CLI commands and Prism interactive interface."""

from pathlib import Path
import pytest
from lantern.cli import main


def test_cli_help(capsys):
    ret = main(["-h"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "lantern" in captured.out.lower()
    assert "Usage:" in captured.out
    assert "Commands:" in captured.out
    assert "Directives Ecosystem:" in captured.out


def test_cli_version(capsys):
    ret = main(["-v"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


def test_cli_status(capsys):
    ret = main(["status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Lantern Status" in captured.out or "lantern" in captured.out.lower()


def test_cli_no_args(capsys):
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Lantern" in captured.out


def test_cli_list(capsys):
    ret = main(["list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Templates" in captured.out
    assert "explainer" in captured.out


def test_cli_new_and_build(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Test lantern new explainer
    ret = main(["new", "demo_explainer", "--template", "explainer"])
    assert ret == 0
    explainer_dir = tmp_path / "demo_explainer"
    assert explainer_dir.exists()
    assert (explainer_dir / "explainer.md").exists()
    assert (explainer_dir / "plot_optimization.py").exists()

    # Test lantern build
    monkeypatch.chdir(explainer_dir)
    ret_build = main(["build", "explainer.md", "--standalone"])
    assert ret_build == 0
    out_html = explainer_dir / "dist" / "explainer.html"
    assert out_html.exists()
    content = out_html.read_text(encoding="utf-8")
    assert "<style>" in content
    assert "Interactive Explainer" in content

    # Test direct file compile (without 'build' subcommand)
    out_custom = explainer_dir / "dist" / "custom.html"
    ret_direct = main(["explainer.md", "-o", str(out_custom)])
    assert ret_direct == 0
    assert out_custom.exists()


def test_cli_new_optimization(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ret = main(["new", "demo_optimization", "--template", "optimization"])
    assert ret == 0
    opt_dir = tmp_path / "demo_optimization"
    assert opt_dir.exists()
    assert (opt_dir / "explainer.md").exists()
    assert (opt_dir / "widgets" / "walker.js").exists()
    assert (opt_dir / "plots" / "plot_rosenbrock.py").exists()
