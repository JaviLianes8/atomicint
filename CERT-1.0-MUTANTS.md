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


## After QA round 1

The five survivors of the independent mutation lens, re-applied to the fixed tree and run
against the contract, copy and message files: all killed.

| Id | Mutation | Result |
| --- | --- | --- |
| M06 | type name cut at 60 characters instead of after | killed: `tests/test_messages.py::test_a_type_name_is_cut_only_past_60_characters[60-False]` |
| M28 | `__index__` turns negative values into 0 | killed: `tests/test_contract_api.py::test_int_and_index_give_the_current_value` |
| M44 | policy cut at 40 characters instead of after | killed: `tests/test_messages.py::test_a_policy_is_cut_only_past_40_characters[40-False]` |
| M47 | slot mangling ignores a leading underscore in the class name | killed: `tests/test_copy.py::test_a_private_slot_of_an_underscored_subclass_is_copied[copy]` |
| M48 | every copy shares one module-wide lock | killed: `tests/test_copy.py::test_a_copy_has_a_lock_of_its_own[copy]` |

22 new mutants over the code written in this round (the lock discipline in `_commit.py`,
the range check under the lock, `__index__` lookup and binding, the `Overflow` docstring),
each alone on a copy of the branch at 4f02eac, full suite with `-x` and a 120 s per-test
limit on another machine (CPython 3.14.2, Node.js present, `ATOMICINT_E2E` unset). All 22
killed. One of them, R05, survived a first run at 69996f5: no test compared equal values
held in different `int` objects, so `test_compare_and_set_compares_values_not_objects`
was added (0641a20) and kills it.

The R mutants change `_commit.py`, `_atomic.py`, `_state.py`, `_bounded.py` and `_coerce.py`.

| Id | Mutation | Result |
| --- | --- | --- |
| R01 | bounded counter takes the unchecked path | killed: `src/atomicint/__init__.py::atomicint` |
| R02 | checked add stores without its check | killed: `tests/test_bounded_stress.py::test_wrap_mode_hands_out_each_sequence_number_equally_often` |
| R03 | update stores without its check | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[False]` |
| R04 | bounded compare applies the policy before comparing | killed: `tests/test_bounded.py::test_a_failed_compare_and_set_never_checks_the_range` |
| R05 | unbounded compare by identity instead of value | killed: `tests/test_atomic.py::test_compare_and_set_compares_values_not_objects[AtomicInt]` |
| R06 | constructor lock not reentrant | killed: per-test time limit (the counter hangs from a finalizer) |
| R07 | lock of a copy not reentrant | killed: per-test time limit (the copy hangs from a finalizer) |
| R08 | store returns the new value | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.get_and_set` |
| R09 | add returns the new value as the previous one | killed: `src/atomicint/__init__.py::atomicint.AtomicInt.get_and_add` |
| R10 | unbounded add reads and stores under two separate locks | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[False]` |
| R11 | integer check trusts `__class__` | killed: `tests/test_inputs.py::test_a_spoofed_class_does_not_get_past_the_checks` |
| R12 | `__index__` called unbound | killed: `tests/test_inputs.py::test_an_index_hook_is_bound_the_way_python_binds_it[odd0-3]` |
| R13 | `__index__` looked up from the base class first | killed: `tests/test_inputs.py::test_the_nearest_index_hook_in_the_class_hierarchy_wins` |
| R14 | hook result checked with `isinstance` | killed: `tests/test_inputs.py::test_an_index_hook_returning_a_non_integer_is_refused[odd0]` |
| R15 | bool input accepted | killed: `tests/test_docs.py::test_every_example_runs_and_prints_its_comments[GUIDE-8]` |
| R16 | bounded compare by identity instead of value | killed: `tests/test_fuzz.py::test_random_programs_match_the_model[1]` |
| R17 | `Overflow` docstring set on the alias typing shares | killed: `tests/test_contract_api.py::test_overflow_has_its_own_docstring_with_a_runnable_example` |
| R18 | `Overflow` example left out of the doctests | killed: `tests/test_contract_api.py::test_overflow_has_its_own_docstring_with_a_runnable_example` |
| R19 | bounded add checks only the lower bound under the lock | killed: `src/atomicint/__init__.py::atomicint` |
| R20 | bounded add skips the range check under the lock | killed: `src/atomicint/__init__.py::atomicint` |
| R21 | lower limit dropped from the range check | killed: `tests/test_bounded.py::test_raise_refuses_an_out_of_range_write_and_keeps_the_value[get_and_add-args2]` |
| R22 | bounded compare never checks the new value | killed: `tests/test_bounded.py::test_raise_refuses_an_out_of_range_write_and_keeps_the_value[compare_and_set-args4]` |
