import threading

from atomicint import AtomicInt


def test_get_returns_the_initial_value() -> None:
    assert AtomicInt(7).get() == 7


def test_default_value_is_zero() -> None:
    assert AtomicInt().get() == 0


def test_set_replaces_the_value() -> None:
    counter = AtomicInt(1)
    counter.set(42)
    assert counter.get() == 42


def test_add_returns_the_new_value() -> None:
    counter = AtomicInt(10)
    assert counter.add(5) == 15
    assert counter.get() == 15


def test_add_accepts_a_negative_amount() -> None:
    counter = AtomicInt(10)
    assert counter.add(-4) == 6


def test_increment_returns_the_new_value() -> None:
    counter = AtomicInt(0)
    assert counter.increment() == 1
    assert counter.increment() == 2


def test_decrement_returns_the_new_value() -> None:
    counter = AtomicInt(3)
    assert counter.decrement() == 2
    assert counter.get() == 2


def test_compare_and_set_swaps_when_the_value_matches() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_set(5, 9) is True
    assert counter.get() == 9


def test_compare_and_set_leaves_the_value_when_it_does_not_match() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_set(4, 9) is False
    assert counter.get() == 5


def test_get_and_set_returns_the_previous_value() -> None:
    counter = AtomicInt(1)
    assert counter.get_and_set(8) == 1
    assert counter.get() == 8


def test_repr_shows_the_current_value() -> None:
    assert repr(AtomicInt(3)) == "AtomicInt(3)"


def test_concurrent_increments_produce_the_exact_total() -> None:
    counter = AtomicInt(0)
    threads_count = 20
    per_thread = 5000
    start = threading.Barrier(threads_count)

    def work() -> None:
        start.wait()
        for _ in range(per_thread):
            counter.increment()

    threads = [threading.Thread(target=work) for _ in range(threads_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert counter.get() == threads_count * per_thread


def test_concurrent_compare_and_set_lets_exactly_one_winner_through() -> None:
    counter = AtomicInt(0)
    threads_count = 20
    winners = AtomicInt(0)
    start = threading.Barrier(threads_count)

    def work() -> None:
        start.wait()
        if counter.compare_and_set(0, 1):
            winners.increment()

    threads = [threading.Thread(target=work) for _ in range(threads_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert winners.get() == 1
    assert counter.get() == 1
