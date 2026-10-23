"""Counters pickled by 0.2.0 load in this version, and new pickles name only the class.

The byte strings below are real output of the 0.2.0 code (commit f173b53 on main),
pickled by CPython 3.13.2 on 2026-10-22 with protocols 0, 2 and 5:
``AtomicInt(41)`` and ``BoundedAtomicInt(7, minimum=0, maximum=9, overflow="wrap")``.
"""

from __future__ import annotations

import pickle
import pickletools

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

V020 = {
    "plain-0": "6361746f6d6963696e742e5f61746f6d69630a5f626c616e6b0a70300a286361746f6d6963696e742e"
    "5f61746f6d69630a41746f6d6963496e740a70310a7470320a5270330a284e286470340a565f76616c75650a"
    "70350a4934310a737470360a622e",
    "bounded-0": "6361746f6d6963696e742e5f61746f6d69630a5f626c616e6b0a70300a286361746f6d6963696e74"
    "2e5f626f756e6465640a426f756e64656441746f6d6963496e740a70310a7470320a5270330a284e28647034"
    "0a565f6d6178696d756d0a70350a49390a73565f6d696e696d756d0a70360a49300a73565f6f766572666c6f"
    "770a70370a56777261700a70380a73565f76616c75650a70390a49370a73747031300a622e",
    "plain-2": "80026361746f6d6963696e742e5f61746f6d69630a5f626c616e6b0a71006361746f6d6963696e742e"
    "5f61746f6d69630a41746f6d6963496e740a71018571025271034e7d710458060000005f76616c756571054b"
    "2973867106622e",
    "bounded-2": "80026361746f6d6963696e742e5f61746f6d69630a5f626c616e6b0a71006361746f6d6963696e74"
    "2e5f626f756e6465640a426f756e64656441746f6d6963496e740a71018571025271034e7d71042858080000"
    "005f6d6178696d756d71054b0958080000005f6d696e696d756d71064b0058090000005f6f766572666c6f77"
    "7107580400000077726170710858060000005f76616c756571094b077586710a622e",
    "plain-5": "80059546000000000000008c1161746f6d6963696e742e5f61746f6d6963948c065f626c616e6b9493"
    "9468008c0941746f6d6963496e74949394859452944e7d948c065f76616c7565944b29738694622e",
    "bounded-5": "8005958e000000000000008c1161746f6d6963696e742e5f61746f6d6963948c065f626c616e6b94"
    "93948c1261746f6d6963696e742e5f626f756e646564948c10426f756e64656441746f6d6963496e74949394"
    "859452944e7d94288c085f6d6178696d756d944b098c085f6d696e696d756d944b008c095f6f766572666c6f"
    "77948c0477726170948c065f76616c7565944b07758694622e",
}


@pytest.mark.parametrize("key", sorted(V020))
def test_a_counter_pickled_by_0_2_0_loads_and_works(key: str) -> None:
    counter = pickle.loads(bytes.fromhex(V020[key]))
    if key.startswith("plain"):
        assert type(counter) is AtomicInt
        assert counter.get() == 41 and counter.increment() == 42
    else:
        assert type(counter) is BoundedAtomicInt
        assert repr(counter) == "BoundedAtomicInt(7, minimum=0, maximum=9, overflow='wrap')"
        assert counter.add(5) == 2


def _globals(data: bytes) -> set[str]:
    """Every module.name a pickle refers to."""
    found: set[str] = set()
    strings: list[str] = []
    for opcode, arg, _ in pickletools.genops(data):
        if opcode.name in ("GLOBAL", "INST"):
            found.add(str(arg).replace(" ", "."))
        elif isinstance(arg, str):
            strings.append(arg)
        if opcode.name == "STACK_GLOBAL":
            found.add(".".join(strings[-2:]))
    return found


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_a_new_pickle_refers_only_to_the_class_and_copyreg(protocol: int) -> None:
    # The class is named where it is defined: the same paths 0.2.0 pickles name, which
    # therefore stay importable for the whole 1.x series. No helper function is named.
    for counter in (AtomicInt(3), BoundedAtomicInt(3, minimum=0, maximum=5, overflow="wrap")):
        names = _globals(pickle.dumps(counter, protocol=protocol))
        cls = type(counter)
        # Protocols 0 and 1 spell the standard copyreg module by its old name.
        assert f"{cls.__module__}.{cls.__name__}" in names
        assert names - {f"{cls.__module__}.{cls.__name__}"} <= {
            "copyreg.__newobj__",
            "copy_reg.__newobj__",
        }
        assert cls.__module__ in ("atomicint._atomic", "atomicint._bounded")
