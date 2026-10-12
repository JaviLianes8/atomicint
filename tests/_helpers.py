"""Thread helpers shared by the test modules."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager


def run_threads(workers: list[Callable[[], None]], timeout: float = 60) -> None:
    """Start every worker together and fail if any raises or is still running at the end."""
    errors: list[BaseException] = []
    start = threading.Barrier(len(workers))

    def wrap(worker: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            try:
                start.wait()
                worker()
            except BaseException as error:
                errors.append(error)

        return run

    threads = [threading.Thread(target=wrap(worker), daemon=True) for worker in workers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout)
    assert all(not thread.is_alive() for thread in threads), "a worker is stuck"
    if errors:
        raise errors[0]


@contextmanager
def tight_switching() -> Iterator[None]:
    """Make the GIL switch threads as often as possible, so races show up quickly."""
    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        yield
    finally:
        sys.setswitchinterval(previous)
