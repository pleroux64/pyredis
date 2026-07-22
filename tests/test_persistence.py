from pyredis.cache import LRUCache
from pyredis.persistence import load_snapshot, save_snapshot
from pyredis.skiplist import SkipList


def test_load_snapshot_returns_none_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_snapshot() is None


def test_save_then_load_roundtrips_cache_and_zsets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = LRUCache(10)
    store.set("name", "patrick")
    store.expire("name", "60")

    zsets = {"leaderboard": SkipList()}
    zsets["leaderboard"].insert(100, "alice")
    zsets["leaderboard"].insert(85, "bob")

    save_snapshot(store, zsets)
    loaded = load_snapshot()

    assert (tmp_path / "snapshot.json").exists()
    assert loaded["cache"]["name"]["value"] == "patrick"
    assert loaded["cache"]["name"]["expiration"] is not None
    assert loaded["zsets"]["leaderboard"] == [
        {"score": 85.0, "member": "bob"},
        {"score": 100.0, "member": "alice"},
    ]
    assert "timestamp" in loaded


def test_save_snapshot_with_no_expiration_serializes_null(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = LRUCache(10)
    store.set("city", "boston")

    save_snapshot(store, {})
    loaded = load_snapshot()

    assert loaded["cache"]["city"]["expiration"] is None
    assert loaded["zsets"] == {}
