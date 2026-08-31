"""Regression tests for the frontend synthetic-source contract."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

VIEW_FILES = [
    ROOT / "app" / "views" / "overview.py",
    ROOT / "app" / "views" / "student_behaviour.py",
    ROOT / "app" / "views" / "course_performance.py",
    ROOT / "app" / "views" / "reports_insights.py",
]


@pytest.mark.parametrize("path", VIEW_FILES)
def test_view_loader_no_longer_hardcodes_raw_path(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_load_dashboard_data"
    ]

    assert len(functions) == 1

    function = functions[0]
    assert function.args.args[0].arg == "data_path"

    default = function.args.defaults[0]
    assert isinstance(default, ast.Constant)
    assert default.value is None


def test_analytics_service_default_is_none():
    path = ROOT / "app" / "services" / "analytics_service.py"
    text = path.read_text(encoding="utf-8")

    assert 'data_path: str | Path | None = None' in text
    assert "load_all_data()" in text
    assert "if self.data_path is None" in text


def test_no_frontend_view_default_references_data_raw():
    for path in VIEW_FILES:
        text = path.read_text(encoding="utf-8")
        assert 'data_path: str = "data/raw"' not in text
