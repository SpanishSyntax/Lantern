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


def test_cli_agent_mode(capsys):
    ret = main(["-h", "--agent"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Lantern v0.1.0" in captured.out
    assert "Commands:" in captured.out
    assert "╭" not in captured.out  # No ASCII box borders
    assert "🏮" not in captured.out


def test_cli_json_mode(capsys):
    import json

    ret = main(["status", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["app"] == "lantern"
    assert "version" in data
    assert "templates" in data

    ret_list = main(["list", "--json"])
    assert ret_list == 0
    captured_list = capsys.readouterr()
    list_data = json.loads(captured_list.out)
    assert "templates" in list_data
    assert "documents" in list_data


def test_cli_export(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["new", "test_export_doc"])
    doc_dir = tmp_path / "test_export_doc"
    monkeypatch.chdir(doc_dir)

    # Export static
    ret_static = main(["export", "explainer.md", "--format", "static"])
    assert ret_static == 0
    static_dist = doc_dir / "dist" / "explainer_static"
    assert (static_dist / "index.html").exists()
    assert (static_dist / "README.md").exists()
    assert (static_dist / "static" / "lantern.css").exists()

    # Export jinja
    ret_jinja = main(["export", "explainer.md", "--format", "jinja"])
    assert ret_jinja == 0
    jinja_dist = doc_dir / "dist" / "explainer_jinja"
    assert (jinja_dist / "app.py").exists()
    assert (jinja_dist / "requirements.txt").exists()
    assert (jinja_dist / "Dockerfile").exists()
    assert (jinja_dist / "templates" / "base.html.j2").exists()
