import random


class SkipListNode:

    def __init__(self, score, member):
        self.score = score
        self.member = member
        self.forward = []


class SkipList:

    def __init__(self):
        self.MAX_LEVELS = 16
        self.PROBABILITY = 0.5
        self.head = SkipListNode(None, None)
        self.head.forward = [None] * self.MAX_LEVELS
        self.cur_max_level = 0

    def random_level(self):
        levels = 1
        while levels < self.MAX_LEVELS:
            flip = random.random()
            if flip < self.PROBABILITY:
                levels +=1
            else:
                return levels
        return levels

    def insert(self, score, member):
        self._remove_if_present(member)

        levels = self.random_level()
        update = [None] * self.MAX_LEVELS
        current = self.head

        for level in range(self.cur_max_level, levels):
            update[level] = self.head

        for level in range(self.cur_max_level - 1, -1, -1):
            while current.forward[level] and current.forward[level].score < score:
                current = current.forward[level]
            update[level] = current



        target = SkipListNode(score, member)
        target.forward = [None] * levels

        for level in range(0, levels):
            dummy = update[level].forward[level]
            update[level].forward[level] = target
            target.forward[level] = dummy

        if levels > self.cur_max_level:
            self.cur_max_level = levels

    def _remove_if_present(self, member):
        current = self.head
        score = None
        while current.forward[0] is not None:
            if current.forward[0].member == member:
                score = current.forward[0].score
                break
            current = current.forward[0]

        if score is None:
            return

        update = [None] * self.MAX_LEVELS
        current = self.head

        for level in range(self.cur_max_level - 1, -1, -1):
            while current.forward[level] and (
                current.forward[level].score < score
                or (current.forward[level].score == score and current.forward[level].member != member)
            ):
                current = current.forward[level]
            update[level] = current

        target = current.forward[0]

        for level in range(self.cur_max_level):
            if update[level].forward[level] is target:
                update[level].forward[level] = target.forward[level]

        while self.cur_max_level > 0 and self.head.forward[self.cur_max_level - 1] is None:
            self.cur_max_level -= 1

    def rank(self, member):
        counter = 0
        current = self.head

        while current.forward[0] is not None:
            if current.forward[0].member == member:
                return counter
            current = current.forward[0]
            counter +=1

        return None

    def get_range(self, start, stop):
        result = []
        current = self.head

        for _ in range(0, start):
            if current.forward[0] is not None:

                current = current.forward[0]
            else:
                break
        if stop == -1:
            while current.forward[0] is not None:
                result.append(current.forward[0].member)
                current = current.forward[0]
            return result
        skips = stop - start + 1

        for _ in range(0, skips):
            if current.forward[0] is not None:
                result.append(current.forward[0].member)
                current = current.forward[0]
            else:
                break

        return result
