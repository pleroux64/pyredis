from pyredis.skiplist import SkipList


def test_rank_reflects_score_order():
    zset = SkipList()
    zset.insert(85, "bob")
    zset.insert(100, "alice")
    zset.insert(92, "charlie")

    assert zset.rank("bob") == 0
    assert zset.rank("charlie") == 1
    assert zset.rank("alice") == 2


def test_rank_missing_member_returns_none():
    zset = SkipList()
    zset.insert(10, "alice")
    assert zset.rank("nobody") is None


def test_rank_on_empty_skiplist_returns_none():
    zset = SkipList()
    assert zset.rank("anyone") is None


def test_get_range_returns_members_in_score_order():
    zset = SkipList()
    zset.insert(85, "bob")
    zset.insert(100, "alice")
    zset.insert(92, "charlie")

    assert zset.get_range(0, 2) == ["bob", "charlie", "alice"]


def test_get_range_subset():
    zset = SkipList()
    zset.insert(85, "bob")
    zset.insert(100, "alice")
    zset.insert(92, "charlie")

    assert zset.get_range(0, 1) == ["bob", "charlie"]
    assert zset.get_range(1, 2) == ["charlie", "alice"]


def test_get_range_out_of_bounds_truncates():
    zset = SkipList()
    zset.insert(10, "solo")
    assert zset.get_range(0, 10) == ["solo"]


def test_get_range_start_past_end_returns_empty():
    zset = SkipList()
    zset.insert(10, "solo")
    assert zset.get_range(5, 10) == []


def test_get_range_stop_negative_one_returns_to_end():
    zset = SkipList()
    zset.insert(85, "bob")
    zset.insert(100, "alice")
    zset.insert(92, "charlie")

    assert zset.get_range(0, -1) == ["bob", "charlie", "alice"]
    assert zset.get_range(1, -1) == ["charlie", "alice"]


def test_get_range_stop_negative_one_on_empty_skiplist_returns_empty():
    zset = SkipList()
    assert zset.get_range(0, -1) == []


def test_get_range_stop_negative_one_with_start_past_end_returns_empty():
    zset = SkipList()
    zset.insert(10, "solo")
    assert zset.get_range(5, -1) == []


def test_reinserting_existing_member_updates_score_instead_of_duplicating():
    zset = SkipList()
    zset.insert(100, "alice")
    zset.insert(85, "bob")
    zset.insert(92, "charlie")

    zset.insert(50, "alice")  # alice's new score should re-sort her, not add a second node

    assert zset.get_range(0, -1) == ["alice", "bob", "charlie"]
    assert zset.rank("alice") == 0


def test_reinserting_same_score_and_member_is_idempotent():
    zset = SkipList()
    zset.insert(10, "solo")
    zset.insert(10, "solo")

    assert zset.get_range(0, -1) == ["solo"]


def test_updating_score_of_only_member_keeps_skiplist_consistent():
    zset = SkipList()
    zset.insert(10, "solo")
    zset.insert(20, "solo")  # exercises cur_max_level shrinking correctly on removal

    assert zset.get_range(0, -1) == ["solo"]
    assert zset.rank("solo") == 0


def test_updating_one_members_score_does_not_affect_others():
    zset = SkipList()
    zset.insert(10, "a")
    zset.insert(20, "b")
    zset.insert(30, "c")

    zset.insert(25, "a")  # move "a" between "b" and "c"

    assert zset.get_range(0, -1) == ["b", "a", "c"]
    assert zset.rank("b") == 0
    assert zset.rank("a") == 1
    assert zset.rank("c") == 2


def test_insert_maintains_order_with_many_members():
    zset = SkipList()
    scores = [50, 10, 40, 20, 30, 5, 45]
    for i, score in enumerate(scores):
        zset.insert(score, f"member{i}")

    expected_order = [f"member{i}" for i, _ in sorted(enumerate(scores), key=lambda p: p[1])]
    assert zset.get_range(0, len(scores) - 1) == expected_order


def test_random_level_within_bounds():
    zset = SkipList()
    for _ in range(200):
        level = zset.random_level()
        assert 1 <= level <= zset.MAX_LEVELS
