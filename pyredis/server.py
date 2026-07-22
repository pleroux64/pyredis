import os
import signal
import socket

from .cache import LRUCache
from .commands import handle_command
from .persistence import load_snapshot
from .protocol import encode_resp, parse_resp
from .skiplist import SkipList


def main():

    HOST = "127.0.0.1"
    PORT = 65432

    cache = LRUCache(10)
    zsets = {}

    data = load_snapshot()
    timestamp = 0
    if data:
        for key, entry in data["cache"].items():
            cache.set(key, entry["value"])
            if entry["expiration"] is not None:
                cache.cache[key].expiration = entry["expiration"]


        for key, entry in data["zsets"].items():
            zsets[key] = SkipList()
            for item in entry:
                zsets[key].insert(item["score"], item["member"])

        timestamp = data["timestamp"]

    exists = os.path.exists("wal.log")

    if exists:
        with open("wal.log") as f:
            for line in f:
                parts = line.strip().split()
                line_timestamp = float(parts[0])
                if line_timestamp > timestamp:

                    handle_command(parts[1:], cache, None, zsets)

    def shutdown(signum, frame):
        log.flush()
        log.close()
        exit(0)


    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    with open("wal.log", "a") as log, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:

            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    parts = parse_resp(data.decode())
                    return_msg = handle_command(parts, cache, log, zsets)
                    conn.sendall(encode_resp(return_msg).encode())


if __name__ == "__main__":
    main()
