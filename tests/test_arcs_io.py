import json
import os
import importlib.util


def _load_module_by_path(name: str, rel_path: str):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


utils = _load_module_by_path("arcs_utils", "arcs_utils.py")
# Ensure the import inside `arcs.py` can resolve `arcs_utils` by placing it into sys.modules
import sys
sys.modules["arcs_utils"] = utils
arcs = _load_module_by_path("arcs", "arcs.py")


def test_save_and_load_json_file(tmp_path):
    fn = tmp_path / "quotes_test.json"
    data = [{"id": 1, "name": "T1", "items": []}]
    utils.save_json_file(str(fn), data)

    loaded = utils.load_json_file(str(fn))
    assert loaded == data


def test_save_quotes_and_load_quotes_respects_user_then_bundled(tmp_path, monkeypatch):
    # Prepare a bundled file and a user file and ensure load_quotes prefers user file
    bundled = tmp_path / "bundled.json"
    user_file = tmp_path / "user.json"

    bundled_data = [{"id": 10, "name": "bundled", "items": []}]
    user_data = [{"id": 20, "name": "user", "items": []}]

    utils.save_json_file(str(bundled), bundled_data)
    utils.save_json_file(str(user_file), user_data)

    # Monkeypatch module-level paths in arcs to point to our temp files
    monkeypatch.setattr(arcs, "BUNDLED_QUOTES_FILE", str(bundled))
    monkeypatch.setattr(arcs, "QUOTES_FILE", str(user_file))

    # When both exist, load_quotes should return user data
    out = arcs.load_quotes()
    assert out == user_data

    # Remove user file to force fallback
    os.remove(str(user_file))
    out2 = arcs.load_quotes()
    assert out2 == bundled_data


def test_save_quotes_writes_user_file(tmp_path, monkeypatch):
    user_file = tmp_path / "quotes_save.json"
    monkeypatch.setattr(arcs, "QUOTES_FILE", str(user_file))

    q = {"id": 42, "name": "Saved Quote", "items": []}
    arcs.save_quotes([q])

    loaded = utils.load_json_file(str(user_file))
    assert loaded[0]["id"] == 42
