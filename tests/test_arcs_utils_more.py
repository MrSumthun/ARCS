import os
import re
import importlib.util


def _load_module_by_path(name: str, rel_path: str):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arcs_utils = _load_module_by_path("arcs_utils", "arcs_utils.py")


def test_safe_filename_unicode_and_length():
    s = "Hello Wörld: /?*<>|\n"
    out = arcs_utils.safe_filename(s)
    # Only allow ASCII safe characters and underscores for others
    assert re.match(r"^[A-Za-z0-9._-]+$", out)
    assert len(out) <= 120


def test_create_quote_with_name_and_defaults():
    q = arcs_utils.create_quote("ACME 2025-12-18")
    assert q["name"].startswith("ACME")
    assert isinstance(q["id"], int)
    assert q["items"] == []


def test_normalize_quote_name_includes_po_when_present():
    q = {"created_at": "2022-08-01T12:00:00+00:00", "po_number": "PO-999"}
    name = arcs_utils.normalize_quote_name(q)
    assert "2022-08-01" in name
    assert "PO-999" in name


def test_get_resource_path_basic():
    # get_resource_path should return a joined path containing the rel_path segments
    rel = os.path.join("data", "quotes.json")
    p = arcs_utils.get_resource_path(rel)
    assert rel in p.replace("\\", "/")
