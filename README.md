# pyredis

[![CI](https://github.com/pleroux64/pyredis/actions/workflows/ci.yml/badge.svg)](https://github.com/pleroux64/pyredis/actions/workflows/ci.yml)

A Redis server clone built from scratch in Python — no external dependencies. Implements the RESP wire protocol, so it's a drop-in target for `redis-cli` and any standard Redis client.

## Features

- **RESP protocol** — parses and encodes the same wire format real Redis uses (`pyredis/protocol.py`)
- **String commands** — `SET`, `GET`, `DEL`, `EXPIRE` backed by a hand-rolled LRU cache with O(1) get/set/evict and lazy TTL expiration (`pyredis/cache.py`)
- **Sorted sets** — `ZADD`, `ZRANK`, `ZRANGE` backed by a skip list (`pyredis/skiplist.py`); `ZADD` on an existing member updates its score in place rather than inserting a duplicate, so it behaves like a real set
- **Durability** — a write-ahead log records every mutation as it happens (flushed to disk on every write) and `SAVE` writes a point-in-time JSON snapshot. On startup the snapshot is loaded first, then the WAL is replayed from that point forward. The server also traps `SIGTERM`/`SIGINT` to flush and close the log before exiting, so a normal shutdown (e.g. `kill`, a container stop) doesn't lose the last writes (`pyredis/persistence.py`, `pyredis/server.py`)
- **Error handling** — malformed or unknown commands return a proper RESP error reply (`-ERR ...`) instead of crashing the process; typed reply objects (`RespOk`, `RespNil`, `RespPong`, `RespError`) keep protocol replies distinct from user data, so `SET k nil` followed by `GET k` correctly returns the bulk string `"nil"` instead of being misread as a missing key (`pyredis/protocol.py`, `pyredis/commands.py`)

## Architecture

```
pyredis/
    __main__.py    entry point for `python -m pyredis`
    server.py       boot sequence (snapshot -> WAL replay) + socket accept loop
    cache.py        Node, LRUCache — doubly linked list + dict, TTL via lazy expiration
    skiplist.py     SkipListNode, SkipList — probabilistic skip list backing sorted sets
    protocol.py     parse_resp, encode_resp — RESP wire format
    persistence.py  save_snapshot, load_snapshot — JSON snapshotting
    commands.py     handle_command — command dispatch table
tests/              pytest suite covering all of the above
```

Each module has a single responsibility and no circular dependencies: `server.py` wires everything together; `commands.py` is the only module that depends on more than one of the data-structure modules. The package is pip-installable (`pyproject.toml`), so it can be imported as `from pyredis.cache import LRUCache` from anywhere, not just when run from the repo root.

## Supported commands

| Command | Example | Notes |
|---|---|---|
| `SET key value` | `SET name patrick` | |
| `GET key` | `GET name` | returns `nil` if missing or expired |
| `DEL key` | `DEL name` | |
| `EXPIRE key seconds` | `EXPIRE name 60` | TTL, checked lazily on `GET` |
| `ZADD key score member` | `ZADD leaderboard 100 alice` | re-adding an existing member updates its score |
| `ZRANK key member` | `ZRANK leaderboard alice` | 0-indexed by ascending score |
| `ZRANGE key start stop` | `ZRANGE leaderboard 0 -1` | inclusive range by rank; `stop=-1` means "to the end" |
| `SAVE` | `SAVE` | writes `snapshot.json` |
| `PING` | `PING` | replies `PONG`; health check, not logged to the WAL |

## Running it

```bash
make install   # pip install -e . plus dev dependencies (pytest, ruff)
make run       # starts the server on 127.0.0.1:65432 (python -m pyredis)
make test      # runs the test suite
make lint      # runs ruff
```

Once running, talk to it with `redis-cli`:

```bash
redis-cli -p 65432
127.0.0.1:65432> SET name patrick
OK
127.0.0.1:65432> GET name
"patrick"
127.0.0.1:65432> ZADD leaderboard 100 alice
OK
127.0.0.1:65432> ZRANGE leaderboard 0 -1
1) "alice"
```

## Design notes

- The LRU cache and skip list are both implemented from first principles (no `functools.lru_cache`, no `collections.OrderedDict`) to demonstrate the underlying data structures.
- Replies are modeled as typed objects (`RespOk`, `RespNil`, `RespPong`, `RespError` in `protocol.py`) rather than magic strings. Early versions used the strings `"OK"`/`"nil"`/`"PONG"` directly as both protocol signals and possible user data, which meant `SET k nil` followed by `GET k` was indistinguishable from a genuinely missing key. `encode_resp` now dispatches on `isinstance()`, so a stored value that happens to equal `"nil"` can never be mistaken for the wire-level nil marker (`$-1\r\n`).
- Malformed input (wrong argument count, non-numeric score/TTL) and unknown commands return a `RespError` — encoded as a real RESP error reply (`-ERR ...\r\n`) — instead of raising an uncaught exception. Since the server handles one connection at a time, an unhandled exception from a single bad command would previously crash the process for every client, not just the one that sent it.
- Sorted sets use a skip list rather than a balanced BST (e.g. red-black/AVL tree), matching real Redis's choice. A BST needs rotations to stay balanced — more intricate to implement correctly and harder to reason about under concurrent access. A skip list gets expected O(log n) search/insert from randomized levels alone, with no rebalancing logic, and range queries (`ZRANGE`) fall out naturally from following the level-0 forward pointers — a BST would need an in-order traversal or extra threading to do the same.
- `ZRANK` currently walks the skip list's bottom level in O(n). A proper O(log n) implementation requires a member→score index (for O(1) score lookup) plus per-level span counters on the skip list nodes (to accumulate rank during the level descent) — a natural next step.
- The server is currently single-threaded/single-connection (one `accept()` loop, no concurrency) — a deliberate scope cut to keep the core data structures and protocol handling as the focus.
- `ZRANGE`'s `stop` supports `-1` for "to the end," matching Redis. Other negative indices (e.g. a negative `start`, or `stop=-2` for "second-to-last") aren't implemented — only the `-1` special case.
- `cache`, `zsets`, and `log` are threaded through `handle_command` as three separate positional arguments rather than bundled into one object. Fine at this size; would get unwieldy if more shared state gets added later — a natural candidate for a small `Store`/`Server` class.
