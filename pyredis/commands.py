import time

from .persistence import save_snapshot
from .protocol import RespError, RespNil, RespOk, RespPong
from .skiplist import SkipList


def handle_command(parts, cache, log, zsets):


    if not parts:
        return ""

    command = parts[0]
    if command == "SAVE":
        save_snapshot(cache, zsets)
        return RespOk()
    if command == "PING":
        return RespPong()

    try:
        return _dispatch(command, parts, cache, log, zsets)
    except (IndexError, ValueError, TypeError):
        return RespError(f"wrong number of arguments or bad value for '{command}' command")


def _dispatch(command, parts, cache, log, zsets):
    key = parts[1]
    value = parts[2] if len(parts) > 2 else None
    return_msg = ""

    if command == "SET":
        if log is not None:

            log.write(str(time.time()) + " " + " ".join(parts) + "\n")
            log.flush()
        cache.set(key, value)  # Store value and expiration time (None for now)
        return_msg = RespOk()

    elif command == "GET":
        result = cache.get(key)

        return_msg = result if result is not None else RespNil()

    elif command == "DEL":
        cache.delete(key)
        if log is not None:

            log.write(str(time.time()) + " " + " ".join(parts) + "\n")
            log.flush()
        return_msg = RespOk()

    elif command == "EXPIRE":
        if log is not None:

            log.write(str(time.time()) + " " + " ".join(parts) + "\n")
            log.flush()
        cache.expire(key,value)
        return_msg = RespOk()

    elif command == "ZADD":

        if key not in zsets:
            zsets[key] = SkipList()
        target = zsets[key]
        member = parts[3]

        target.insert(float(value),member)

        if log is not None:

            log.write(str(time.time()) + " " + " ".join(parts) + "\n")
            log.flush()
        return_msg = RespOk()

    elif command == "ZRANK":
        if key not in zsets:
            return_msg = RespNil()
        else:

            target = zsets[key]

            result = target.rank(value)
            return_msg = RespNil() if result is None else str(result)

    elif command == "ZRANGE":
        if key not in zsets:
            return_msg = RespNil()
        else:

            target = zsets[key]
            start = int(parts[2])
            stop = int(parts[3])

            return_msg = target.get_range(start, stop)

    else:
        return RespError(f"unknown command '{command}'")

    return return_msg
