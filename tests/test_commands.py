import io

from pyredis.cache import LRUCache
from pyredis.commands import handle_command
from pyredis.persistence import load_snapshot
from pyredis.protocol import RespError, RespNil, RespOk, RespPong, encode_resp


def test_empty_command_returns_empty_string():
    assert handle_command([], LRUCache(10), None, {}) == ""


def test_storing_literal_sentinel_words_as_data_does_not_collide_with_protocol_replies():
    # regression test: encode_resp(handle_command(...)) is what a client actually
    # receives on the wire. SET-ing the literal strings "OK"/"nil"/"PONG" must
    # come back as real bulk-string data, not get misread as a status/nil/pong reply.
    store = LRUCache(10)
    for word, expected_wire in (
        ("OK", "$2\r\nOK\r\n"),
        ("nil", "$3\r\nnil\r\n"),
        ("PONG", "$4\r\nPONG\r\n"),
    ):
        handle_command(["SET", "k", word], store, None, {})
        result = handle_command(["GET", "k"], store, None, {})
        assert encode_resp(result) == expected_wire


def test_ping_returns_pong():
    assert isinstance(handle_command(["PING"], LRUCache(10), None, {}), RespPong)


def test_unknown_command_returns_resp_error():
    result = handle_command(["NOTACOMMAND", "x"], LRUCache(10), None, {})
    assert isinstance(result, RespError)


def test_missing_argument_returns_resp_error_instead_of_crashing():
    # bare GET with no key -> parts[1] would raise IndexError
    result = handle_command(["GET"], LRUCache(10), None, {})
    assert isinstance(result, RespError)


def test_non_numeric_zadd_score_returns_resp_error_instead_of_crashing():
    # float("abc") would raise ValueError
    result = handle_command(["ZADD", "lb", "abc", "alice"], LRUCache(10), None, {})
    assert isinstance(result, RespError)


def test_expire_with_missing_seconds_returns_resp_error_instead_of_crashing():
    # int(None) would raise TypeError
    store = LRUCache(10)
    handle_command(["SET", "k", "v"], store, None, {})
    result = handle_command(["EXPIRE", "k"], store, None, {})
    assert isinstance(result, RespError)


def test_server_keeps_working_after_a_bad_command():
    store = LRUCache(10)
    handle_command(["GET"], store, None, {})  # would previously have crashed the process
    assert isinstance(handle_command(["SET", "name", "patrick"], store, None, {}), RespOk)
    assert handle_command(["GET", "name"], store, None, {}) == "patrick"


def test_set_then_get():
    store = LRUCache(10)
    assert isinstance(handle_command(["SET", "name", "patrick"], store, None, {}), RespOk)
    assert handle_command(["GET", "name"], store, None, {}) == "patrick"


def test_get_missing_key_returns_nil():
    store = LRUCache(10)
    assert isinstance(handle_command(["GET", "missing"], store, None, {}), RespNil)


def test_del_removes_key():
    store = LRUCache(10)
    handle_command(["SET", "name", "patrick"], store, None, {})
    assert isinstance(handle_command(["DEL", "name"], store, None, {}), RespOk)
    assert isinstance(handle_command(["GET", "name"], store, None, {}), RespNil)


def test_expire_then_get_before_ttl(monkeypatch):
    from pyredis import cache as cache_module

    store = LRUCache(10)
    monkeypatch.setattr(cache_module.time, "time", lambda: 1000.0)
    handle_command(["SET", "session", "abc"], store, None, {})
    handle_command(["EXPIRE", "session", "60"], store, None, {})

    assert handle_command(["GET", "session"], store, None, {}) == "abc"


def test_zadd_zrank_zrange():
    store = LRUCache(10)
    zsets = {}
    handle_command(["ZADD", "lb", "100", "alice"], store, None, zsets)
    handle_command(["ZADD", "lb", "85", "bob"], store, None, zsets)
    handle_command(["ZADD", "lb", "92", "charlie"], store, None, zsets)

    assert handle_command(["ZRANK", "lb", "bob"], store, None, zsets) == "0"
    assert handle_command(["ZRANK", "lb", "alice"], store, None, zsets) == "2"
    assert handle_command(["ZRANGE", "lb", "0", "2"], store, None, zsets) == [
        "bob", "charlie", "alice",
    ]


def test_zadd_on_existing_member_updates_score_instead_of_duplicating():
    store = LRUCache(10)
    zsets = {}
    handle_command(["ZADD", "lb", "100", "alice"], store, None, zsets)
    handle_command(["ZADD", "lb", "85", "bob"], store, None, zsets)

    handle_command(["ZADD", "lb", "1", "alice"], store, None, zsets)  # re-add with new score

    assert handle_command(["ZRANGE", "lb", "0", "-1"], store, None, zsets) == ["alice", "bob"]
    assert handle_command(["ZRANK", "lb", "alice"], store, None, zsets) == "0"


def test_zrange_with_negative_one_stop_returns_to_end():
    store = LRUCache(10)
    zsets = {}
    handle_command(["ZADD", "lb", "100", "alice"], store, None, zsets)
    handle_command(["ZADD", "lb", "85", "bob"], store, None, zsets)
    handle_command(["ZADD", "lb", "92", "charlie"], store, None, zsets)

    assert handle_command(["ZRANGE", "lb", "0", "-1"], store, None, zsets) == [
        "bob", "charlie", "alice",
    ]


def test_zrank_on_missing_key_returns_nil():
    store = LRUCache(10)
    assert isinstance(handle_command(["ZRANK", "lb", "alice"], store, None, {}), RespNil)


def test_zrank_on_missing_member_returns_nil():
    store = LRUCache(10)
    zsets = {}
    handle_command(["ZADD", "lb", "100", "alice"], store, None, zsets)
    assert isinstance(handle_command(["ZRANK", "lb", "nobody"], store, None, zsets), RespNil)


def test_zrange_on_missing_key_returns_nil():
    store = LRUCache(10)
    assert isinstance(handle_command(["ZRANGE", "lb", "0", "1"], store, None, {}), RespNil)


def test_mutating_commands_append_to_log():
    store = LRUCache(10)
    log = io.StringIO()

    handle_command(["SET", "name", "patrick"], store, log, {})
    handle_command(["DEL", "name"], store, log, {})

    lines = log.getvalue().strip().splitlines()
    assert len(lines) == 2
    assert lines[0].endswith("SET name patrick")
    assert lines[1].endswith("DEL name")


def test_get_does_not_write_to_log():
    store = LRUCache(10)
    log = io.StringIO()

    handle_command(["SET", "name", "patrick"], store, log, {})
    handle_command(["GET", "name"], store, log, {})

    assert len(log.getvalue().strip().splitlines()) == 1


def test_save_command_writes_snapshot_and_returns_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = LRUCache(10)
    zsets = {}
    handle_command(["SET", "name", "patrick"], store, None, zsets)

    assert isinstance(handle_command(["SAVE"], store, None, zsets), RespOk)
    assert load_snapshot()["cache"]["name"]["value"] == "patrick"
