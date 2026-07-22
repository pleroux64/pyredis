import time


class Node:
    def __init__(self, key, value, expiration=None):
        self.key = key
        self.value = value
        self.expiration = expiration
        self.next = None
        self.prev = None


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = Node(None, None)
        self.tail = Node(None, None)

        self.head.next = self.tail
        self.tail.prev = self.head

    def insert(self, node):
        dummy = self.tail.prev
        node.prev = dummy
        node.next = self.tail
        self.tail.prev = node
        dummy.next = node

    def remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def get(self, key):
        if key in self.cache:
            if self.cache[key].expiration is not None and self.cache[key].expiration < time.time():
                self.delete(key)
                return None
            else:
                self.remove(self.cache[key])
                self.insert(self.cache[key])
                return self.cache[key].value
        else:
            return None

    def set(self, key, value):
        if key in self.cache:
            self.remove(self.cache[key])
            self.insert(self.cache[key])
            self.cache[key].value = value

        else:
            target = Node(key, value)
            self.cache[key] = target
            self.insert(target)
            if len(self.cache) > self.capacity:
                lru = self.head.next
                del self.cache[self.head.next.key]
                self.remove(lru)

    def delete(self, key):
        if key in self.cache:

            target = self.cache[key]
            del self.cache[key]
            self.remove(target)

    def expire(self, key, value):
        if key in self.cache:
            expiration_time = int(value)  # Assuming value is the expiration time in seconds
            self.cache[key].expiration = time.time() + expiration_time
