from pyredis.protocol import RespError, RespNil, RespOk, RespPong, encode_resp, parse_resp


def test_parse_resp_single_arg_command():
    raw = "*1\r\n$4\r\nSAVE\r\n"
    assert parse_resp(raw) == ["SAVE"]


def test_parse_resp_multi_arg_command():
    raw = "*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    assert parse_resp(raw) == ["SET", "foo", "bar"]


def test_parse_resp_zadd_command():
    raw = "*4\r\n$4\r\nZADD\r\n$2\r\nlb\r\n$3\r\n100\r\n$5\r\nalice\r\n"
    assert parse_resp(raw) == ["ZADD", "lb", "100", "alice"]


def test_encode_resp_ok():
    assert encode_resp(RespOk()) == "+OK\r\n"


def test_encode_resp_nil():
    assert encode_resp(RespNil()) == "$-1\r\n"


def test_encode_resp_pong():
    assert encode_resp(RespPong()) == "+PONG\r\n"


def test_encode_resp_error():
    assert encode_resp(RespError("unknown command 'FOO'")) == "-ERR unknown command 'FOO'\r\n"


def test_encode_resp_does_not_confuse_raw_string_data_with_protocol_markers():
    # regression test: these string values are valid user data (e.g. `SET k nil`),
    # and must be encoded as ordinary bulk strings, not mistaken for RespNil/RespOk/RespPong.
    assert encode_resp("OK") == "$2\r\nOK\r\n"
    assert encode_resp("nil") == "$3\r\nnil\r\n"
    assert encode_resp("PONG") == "$4\r\nPONG\r\n"


def test_encode_resp_bulk_string():
    assert encode_resp("patrick") == "$7\r\npatrick\r\n"


def test_encode_resp_list():
    assert encode_resp(["alice", "bob"]) == "*2\r\n$5\r\nalice\r\n$3\r\nbob\r\n"


def test_encode_resp_empty_list():
    assert encode_resp([]) == "*0\r\n"


def test_encode_then_parse_roundtrip_for_command_shape():
    encoded = encode_resp(["SET", "foo", "bar"])
    assert parse_resp(encoded) == ["SET", "foo", "bar"]
