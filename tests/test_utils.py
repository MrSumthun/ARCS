import os
import importlib.util


def _load_utils():
    """Dynamically load the local `arcs_utils` module by path for tests."""
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "arcs_utils.py")
    )
    spec = importlib.util.spec_from_file_location("arcs_utils", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


module = _load_utils()
safe_filename = module.safe_filename
normalize_quote_name = module.normalize_quote_name
create_quote = module.create_quote


def test_safe_filename_basic():
    assert safe_filename("Hello World.txt") == "Hello_World.txt"
    assert safe_filename("a" * 200).startswith("a")


def test_normalize_quote_name_with_date():
    q = {"created_at": "2021-12-01T12:00:00+00:00"}
    assert "2021-12-01" in normalize_quote_name(q)


def test_create_quote_has_expected_fields():
    q = create_quote("Acme 2025-12-01")
    assert isinstance(q.get("id"), int)
    assert "created_at" in q
    assert q.get("items") == []
    assert q.get("name").startswith("Acme") or q.get("name").startswith("ARCS")
