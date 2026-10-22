# atomicint 1.0.0: author mutation round

45 mutants over every module of `src/atomicint`, written before the run (not chosen from
coverage). Each was applied alone to a copy of `release/1.0.0` at 4d3f9ec and the full
suite run with `-x` and a 300 s per-test limit on another machine (CPython 3.14.2,
Java 21.0.12 and Node.js 25.5.0 on the PATH, the fetched reference files present,
`ATOMICINT_E2E` unset). The first failing test is listed. 44 were killed at once; the one
survivor showed a missing contract, which was added and kills it.

Ids: C `_coerce.py`, A `_atomic.py`, S `_state.py`, B `_bounded.py`, I `__init__.py`.

| Id | Mutation | Result |
| --- | --- | --- |
| C1 | bool accepted as an integer | killed: `tests/test_docs.py::test_every_example_runs_and_prints_its_comments[GUIDE-8]` |
| C2 | __index__ returning True accepted | killed: `tests/test_inputs.py::test_an_index_hook_returning_a_non_integer_is_refused[odd0]` |
| C3 | int subclass stored as given | killed: `tests/test_inputs.py::test_an_int_subclass_is_stored_as_a_plain_int` |
| C4 | __index__ int subclass result stored as given | killed: `tests/test_inputs.py::test_an_index_hook_returning_an_int_subclass_is_stored_as_a_plain_int` |
| C5 | long class name copied into the message | killed: `tests/test_messages.py::test_a_very_long_type_name_is_cut_short` |
| C6 | off by one at the exact-digits limit | killed: `tests/test_messages.py::test_a_value_up_to_120_bits_is_written_out_in_full` |
| C7 | sign dropped from a described value | killed: `tests/test_messages.py::test_an_out_of_range_huge_value_raises_overflow_error_with_its_size[-10**5000]` |
| C8 | repr limit off by one | killed: `tests/test_messages.py::test_repr_writes_values_up_to_1800_bits_and_never_fails` |
| A1 | get_and_add returns the new value | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.get_and_add` |
| A2 | add returns the old value | killed: `src/atomicint/__init__.py::atomicint` |
| A3 | increment returns the old value | killed: `src/atomicint/__init__.py::atomicint.AtomicInt` |
| A4 | decrement adds one | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.decrement` |
| A5 | get_and_set skips the range check | killed: `tests/test_bounded.py::test_raise_refuses_an_out_of_range_write_and_keeps_the_value[get_and_set-args3]` |
| A6 | compare inverted | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.compare_and_exchange` |
| A7 | compare_and_exchange returns the value after | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.compare_and_exchange` |
| A8 | expect converted twice | killed: `tests/test_inputs.py::test_compare_and_set_reads_expect_once_and_reports_the_swap` |
| A9 | update commits over a concurrent write | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[False]` |
| A10 | update returns the unfitted result | killed: `tests/test_bounded.py::test_saturate_clamps_to_the_nearest_bound` |
| A11 | input converted while holding the lock | killed: `tests/test_fuzz.py::test_an_index_hook_may_use_the_counter_because_it_runs_before_the_lock` |
| A12 | get_and_add without the lock | killed: `tests/test_bounded_stress.py::test_wrap_mode_hands_out_each_sequence_number_equally_often` |
| A13 | compare_and_exchange without the lock | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[False]` |
| A14 | update commit without the lock | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[False]` |
| A15 | repr ignores the subclass name | killed: `tests/test_copy.py::test_a_subclass_survives_a_copy_and_shows_its_own_name` |
| A16 | 0.2.0 pickles no longer load | killed: `tests/test_upgrade.py::test_a_counter_pickled_by_0_2_0_loads_and_works[bounded-0]` |
| A17 | default value changed | killed: `src/atomicint/__init__.py::atomicint.AtomicInt` |
| S1 | private slot names not mangled | killed: `tests/test_copy.py::test_a_subclass_with_its_own_constructor_keeps_every_attribute[copy]` |
| S2 | a slot left out of copies | killed: `tests/test_copy.py::test_every_pickle_protocol_round_trips_a_bounded_counter` |
| S3 | instance dictionary dropped from copies | killed: `tests/test_copy.py::test_a_subclass_without_slots_keeps_its_instance_attributes[copy]` |
| S4 | copies get no lock | killed: `tests/test_copy.py::test_a_copy_keeps_the_value_but_not_the_identity[copy]` |
| S5 | copies lose the subclass | killed: `tests/test_copy.py::test_every_pickle_protocol_round_trips_a_bounded_counter` |
| B1 | single-value range refused | killed: `tests/test_bounded.py::test_a_single_value_range_is_allowed` |
| B2 | str subclass policy accepted | killed: `tests/test_bounded.py::test_the_overflow_policy_must_be_one_of_the_exact_names[raise]` |
| B3 | wrap with one bound accepted | killed: `tests/test_bounded.py::test_bad_configuration_is_rejected[kwargs2-needs` |
| B4 | minimum itself out of range | killed: `tests/test_bounded.py::test_raise_allows_both_bounds_exactly` |
| B5 | saturate clamps to the wrong bound | killed: `src/atomicint/__init__.py::atomicint` |
| B6 | wrap period off by one | killed: `src/atomicint/__init__.py::atomicint.BoundedAtomicInt` |
| B7 | wrap ignores the offset | killed: `tests/test_bounded.py::test_wrap_on_a_signed_range` |
| B8 | message copies a huge value | killed: `tests/test_docs.py::test_every_example_runs_and_prints_its_comments[GUIDE-8]` |
| B9 | minimum property returns the maximum | killed: `src/atomicint/__init__.py::atomicint.BoundedAtomicInt.minimum` |
| B10 | repr writes mid-size bounds by size | survived; the contract `tests/test_messages.py::test_repr_writes_bounds_up_to_1800_bits_in_full_too` added in b9c1f15 kills it (re-run on that file) |
| B11 | cut policy not marked | killed: `tests/test_messages.py::test_a_bad_policy_is_named_briefly[long]` |
| B12 | default policy changed | killed: `src/atomicint/__init__.py::atomicint.BoundedAtomicInt` |
| B13 | raise policy no longer raises | killed: `src/atomicint/__init__.py::atomicint.BoundedAtomicInt` |
| I1 | classes report the private module | killed: `tests/test_contract_api.py::test_the_classes_belong_to_the_package_and_use_slots` |
| I2 | Overflow left out of __all__ | killed: `tests/test_contract.py::test_all_lists_exactly_the_public_api` |
