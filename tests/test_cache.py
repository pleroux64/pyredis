from pyredis import cache as cache_module
from pyredis.cache import LRUCache


def test_set_and_get_roundtrip():
    store = LRUCache(10)
    store.set("name", "patrick")
    assert store.get("name") == "patrick"


def test_get_missing_key_returns_none():
    store = LRUCache(10)
    assert store.get("missing") is None


def test_set_overwrites_existing_value():
    store = LRUCache(10)
    store.set("name", "patrick")
    store.set("name", "patricio")
    assert store.get("name") == "patricio"
    assert len(store.cache) == 1


def test_delete_removes_key():
    store = LRUCache(10)
    store.set("name", "patrick")
    store.delete("name")
    assert store.get("name") is None


def test_delete_missing_key_is_noop():
    store = LRUCache(10)
    store.delete("missing")  # should not raise
    assert len(store.cache) == 0


def test_eviction_at_capacity_removes_least_recently_used():
    store = LRUCache(2)
    store.set("a", 1)
    store.set("b", 2)
    store.set("c", 3)  # evicts "a", the LRU entry

    assert store.get("a") is None
    assert store.get("b") == 2
    assert store.get("c") == 3
    assert len(store.cache) == 2


def test_get_refreshes_recency_and_protects_from_eviction():
    store = LRUCache(2)
    store.set("a", 1)
    store.set("b", 2)
    store.get("a")       # "a" is now most-recently-used
    store.set("c", 3)    # "b" is now LRU and should be evicted instead

    assert store.get("b") is None
    assert store.get("a") == 1
    assert store.get("c") == 3


def test_expire_sets_expiration_timestamp(monkeypatch):
    store = LRUCache(10)
    store.set("session", "abc")

    monkeypatch.setattr(cache_module.time, "time", lambda: 1000.0)
    store.expire("session", "60")

    assert store.cache["session"].expiration == 1060.0


def test_expired_key_returns_none_and_is_evicted(monkeypatch):
    store = LRUCache(10)
    monkeypatch.setattr(cache_module.time, "time", lambda: 1000.0)
    store.set("session", "abc")
    store.expire("session", "60")

    monkeypatch.setattr(cache_module.time, "time", lambda: 2000.0)  # far past expiry
    assert store.get("session") is None
    assert "session" not in store.cache


def test_unexpired_key_survives_get(monkeypatch):
    store = LRUCache(10)
    monkeypatch.setattr(cache_module.time, "time", lambda: 1000.0)
    store.set("session", "abc")
    store.expire("session", "60")

    monkeypatch.setattr(cache_module.time, "time", lambda: 1030.0)  # within TTL
    assert store.get("session") == "abc"
