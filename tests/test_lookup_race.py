"""A hook looked up while another thread adds and deletes it, on a free-threaded build.

Without the GIL another thread can change a class between any two reads of its
dictionary. The lookup reads each class once, so the counter takes the hook or refuses
the value with the documented ``TypeError``, and never lets a ``KeyError`` out.
"""

from __future__ import annotations

import sysconfig
import threading
from collections.abc import Callable
from typing import Any

import pytest

from atomicint import AtomicInt

pytestmark = pytest.mark.skipif(
    not sysconfig.get_config_var("Py_GIL_DISABLED"), reason="needs a free-threaded build"
)

CALLS = 100_000


def _churn(cls: Any, name: str, attribute: object) -> Callable[[], None]:
    stop = threading.Event()

    def run() -> None:
        while not stop.is_set():
            setattr(cls, name, attribute)
            delattr(cls, name)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()

    def finish() -> None:
        stop.set()
        worker.join(timeout=10)

    return finish


def test_an_index_hook_deleted_by_another_thread_is_taken_or_refused() -> None:
    number: Any = type("Number", (), {})
    finish = _churn(number, "__index__", lambda self: 3)
    taken = refused = 0
    try:
        for _ in range(CALLS):
            try:
                assert AtomicInt(number()).get() == 3
                taken += 1
            except TypeError:
                refused += 1
    finally:
        finish()
    assert taken + refused == CALLS


class Hook:
    def __call__(self, *args: object) -> int:
        return 3


def test_a_get_deleted_by_another_thread_binds_or_calls_the_hook() -> None:
    # With __get__ the hook is bound, without it the hook is called as it is: 3 either way.
    hook: Any = type("Hook", (Hook,), {})
    number: Any = type("Number", (), {"__index__": hook()})
    finish = _churn(hook, "__get__", lambda self, value, owner: self)
    try:
        for _ in range(CALLS):
            assert AtomicInt(number()).get() == 3
    finally:
        finish()
