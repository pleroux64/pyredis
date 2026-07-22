class RespError:
    def __init__(self, message):
        self.message = message


class RespOk:
    pass


class RespNil:
    pass


class RespPong:
    pass


def parse_resp(data):
    result = []
    lines = data.split("\r\n")

    num_elem = int(lines[0][1:])
    index = 1
    for _ in range(num_elem):
        target = lines[index + 1]
        result.append(target)
        index +=2

    return result


def encode_resp(value):
    if isinstance(value, RespError):
        return f"-ERR {value.message}\r\n"
    if isinstance(value, RespOk):
        return "+OK\r\n"
    if isinstance(value, RespNil):
        return "$-1\r\n"
    if isinstance(value, RespPong):
        return "+PONG\r\n"
    if isinstance(value, list):
        result = f"*{len(value)}\r\n"
        for item in value:
            result += f"${len(item)}\r\n{item}\r\n"
        return result

    length = len(value)
    return f"${length}\r\n{value}\r\n"
