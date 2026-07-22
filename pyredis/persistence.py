import json
import os
import time


def save_snapshot(cache, zsets):
    cache_data = {}
    for key, node in cache.cache.items():
        cache_data[key] = {"value": node.value, "expiration": node.expiration}

    zsets_data = {}
    for key, skiplist in zsets.items():
        members = []

        current = skiplist.head
        while current.forward[0] is not None:
            members.append({
                "score": current.forward[0].score,
                "member": current.forward[0].member
            })
            current = current.forward[0]
        zsets_data[key] = members

    with open("snapshot.json", "w") as f:
        data = {
            "timestamp" : time.time(),
            "cache": cache_data,
            "zsets": zsets_data
        }
        json.dump(data, f)


def load_snapshot():
    exists = os.path.exists("snapshot.json")
    if exists:
        with open("snapshot.json") as f:
            return json.load(f)
    else:
        return None
