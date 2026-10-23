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

## After QA round 2

The four survivors of the mutation lens and three mutants of the code changed in this
round, each alone on a copy of the fixed tree, `tests` with `-x` and a 120 s per-test limit
on this PC (CPython 3.13.2, Java 21.0.8 and Node.js present, fetched reference files
absent, `ATOMICINT_E2E` unset). All killed, each by the contract added for it.

| Id | Mutation | Result |
| --- | --- | --- |
| X33 | out-of-range compare-and-set stops retrying once the policy was applied | killed: `tests/test_races.py::test_a_compare_and_set_that_loses_to_an_equal_write_still_stores[saturate-2000]` |
| X31 | update function and policy run with the lock held | killed: `tests/test_update.py::test_the_function_runs_without_the_lock[update]` |
| X62 | bounds in an `OverflowError` written in full up to 1800 bits | killed: `tests/test_messages.py::test_bounds_past_120_bits_are_described_by_their_size` |
| X13 | `__weakref__` slot copied like any other | killed: `tests/test_copy.py::test_a_weakly_referenced_subclass_is_copied[copy]` |
| Q01 | private slots of a `_`-only class name mangled anyway | killed: `tests/test_copy.py::test_a_private_slot_of_an_underscored_subclass_is_copied[copy-_]` |
| Q02 | wrongly typed policy raises `ValueError` | killed: `tests/test_bounded.py::test_a_policy_that_is_not_a_plain_str_raises_type_error[raise]` |
| Q03 | classes reported as `atomicint` again | killed: `tests/test_contract_api.py::test_the_classes_use_slots_and_name_the_module_that_defines_them` |

## After the QA round 2 re-check

The fix of lens c's F4 replaced the slot name mangling with a lookup of the member
descriptors Python created, so S1, M47 and Q01 above mutate code that no longer exists.
Each mutant below was applied alone and run against `tests` or the copy tests on this PC
(CPython 3.13.2). Lens e's N2 to N7 were applied to the 08186fc `_state.py` they target and run
against `tests/test_copy_slots.py` without the iterator and renamed cases (which that
code fails anyway); the rest were applied to the fixed tree.

| Id | Mutation | Result |
| --- | --- | --- |
| N1-P30 | in-range compare calls `self._within(seen)` under the lock | killed: `tests/test_lock_calls.py::test_no_operation_makes_a_call_while_it_holds_the_lock[cas_won-plain]` |
| N2-P13 | private slots mangled with the leaf class name | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Child]` |
| N3-P18 | private slots mangled with `__qualname__` | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Outer.Inner]` |
| N4-P19 | trailing underscores stripped from the class name too | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Tag_]` |
| N5-P16 | names ending in `__` mangled | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Meta]` |
| N6-P17 | a one-string `__slots__` iterated by character | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-One]` |
| N7-P20 | a `__dict__` slot copied like any other | killed: `tests/test_copy_slots.py::test_a_declared_instance_dict_is_copied_not_shared[copy]` |
| N8-P33 | bounds written in full up to 121 bits | killed: `tests/test_messages.py::test_bounds_past_120_bits_are_described_by_their_size` |
| T1 | any attribute with `__get__` taken as a slot | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Streamed]` |
| T2 | the lock copied with the slots | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[deepcopy-Streamed]` |
| T3 | only the leaf class searched | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-StreamedGauge]` |
| T4 | the leaf class skipped | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-Streamed]` |
| T5 | leading underscores stripped from the slot name | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[copy-StreamedGauge]` |
| T6 | the instance dictionary left out | killed: `tests/test_copy.py::test_a_subclass_without_slots_keeps_its_instance_attributes[copy]` |

## After QA round 3

The fix of lens c's F5 to F7 stores each class's slot names when the class is made. Each
mutant below was applied alone to a copy of the fixed tree and run with `-x` against the
copy and lock-call tests on this PC (CPython 3.13.2). V01, V04, V06, M02 and M19 are lens
e's survivors from round 3.

| Id | Mutation | Result |
| --- | --- | --- |
| V01 | in-range compare written `if bool(seen == wanted):` | killed: `tests/test_lock_calls.py::test_no_operation_makes_a_call_while_it_holds_the_lock[cas_won-plain]` |
| V04 | `_store` writes `int(new)` | killed: `tests/test_lock_calls.py::test_no_operation_makes_a_call_while_it_holds_the_lock[set-plain]` |
| V06 | `_apply` reads `int(self._value)` under the lock | killed: `tests/test_lock_calls.py::test_no_operation_makes_a_call_while_it_holds_the_lock[update-plain]` |
| M02 | only the class and its direct bases searched | killed: `tests/test_copy_slots.py::test_inherited_and_wrapped_slots_are_kept[copy-QuietLeaf]` |
| M19 | slots restored through the subclass's `setattr` | killed: `tests/test_copy_slots.py::test_a_copy_is_rebuilt_past_the_subclass_setattr[copy]` |
| S1 | class dictionaries read without a copy | killed: `tests/test_copy_cost.py::test_a_copy_is_safe_while_another_thread_changes_the_class[copy-Unhooked]` |
| S2 | names not stored when the class is made | killed: `tests/test_copy_slots.py::test_inherited_and_wrapped_slots_are_kept[copy-Wrapped]` |
| S3 | stored names ignored, worked out on every copy | equivalent: the walk starts at the class's own stored tuple, so the names are the same and only a constant cost is added |
| S4 | the lock copied with the slots | killed: `tests/test_copy_slots.py::test_every_declared_slot_is_kept[deepcopy-Streamed]` |
| S5 | the bases' stored names ignored when a class is made | killed: `tests/test_copy_slots.py::test_inherited_and_wrapped_slots_are_kept[copy-WrappedChild]` |

## After QA round 4

The fix of lens c's N1 to N3 keeps each class's slot names in a table keyed by the class
(not on the class), adds the names listed in `__slots__`, and skips the bases a stored
tuple already covers. Each `_state.py` mutant below was applied alone to a copy of the
fixed tree and run with `-x` against the copy, class hook and API tests on this PC
(CPython 3.13.2). S06, S09, S12 and S15 are lens e's survivors from round 4, written
against the new code. The `_commit.py` mutants were run with the new finalizer program on
CPython 3.10.19 and 3.11.5 (on 3.12 and later the collector does not start inside an
allocation, so such a mutant cannot lose an update there); the fixed tree passes it on
both.

| Id | Mutation | Result |
| --- | --- | --- |
| V19 | `_store` writes `self._value, = {new}` (a set made under the lock) | killed: `tests/test_reentry_lost.py::test_no_update_from_a_finalizer_is_lost_during_any_operation[get_and_set]` (all four counters lose updates on 3.10 and 3.11) |
| V20 | the in-range compare-and-set stores `self._value, = {replacement}` | killed: `[compare_and_set]` and `[compare_and_exchange]` of the same test |
| W1 | the unbounded add stores through a set | killed: `[add]` and `[get_and_add]` (plain counter) |
| W2 | the bounded in-range add stores through a set | killed: `[add]` and `[get_and_add]` (the three bounded counters) |
| W3 | the update store goes through a set | killed: `[update]` and `[get_and_update]` |
| S06 | a class with no names of its own takes the first stored tuple up its hierarchy | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-QuietChild.extra]` |
| S09 | `Copyable.__init_subclass__` does not chain to `super()` | killed: `tests/test_class_hooks.py::test_a_mixin_class_hook_after_the_counter_still_runs[AtomicInt]` |
| S12 | `_collect` reads the slots of the copied class at every level | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-QuietHeir.own]` |
| S15 | `_collect` de-duplicates through a list | killed: `tests/test_copy_cost.py::test_the_first_copy_under_a_base_that_skipped_the_hook_costs_one_pass` |
| R1 | a stored tuple covers only its own class | killed: `tests/test_copy_cost.py::test_making_a_class_costs_about_what_python_takes_whatever_the_depth` |
| R2 | the names listed in `__slots__` left out | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-Checked.tag]` |
| R3 | listed private names not mangled | killed: `[copy-Private._Private__tag]` of the same test |
| R4 | leading underscores of the class name kept when mangling | killed: `[copy-_Hidden._Hidden__tag]` |
| R5 | names under a hook-skipping base not kept after the first copy | killed: `tests/test_class_hooks.py::test_under_a_base_that_skipped_the_hook_the_names_are_kept_from_the_first_copy` |
| R6 | a one-string `__slots__` not read again | killed: `[copy-_Hidden._Hidden__tag]` |
| R7 | covered bases not skipped | killed: `tests/test_copy_cost.py::test_making_a_class_costs_about_what_python_takes_whatever_the_depth` |
| R8 | a listed `__dict__` taken for a slot | killed: `tests/test_copy_slots.py::test_a_declared_instance_dict_is_copied_not_shared[copy]` |
| R9 | a dict `__slots__` not read again | killed: `[copy-Documented.tag]` |

## After the identity fix (lens e's round 5 probes)

The slot names of each class are now kept by the class's identity (`id()` and a weak
reference whose callback removes the entry when the class dies), not in a
`WeakKeyDictionary`, and `_collect` tracks covered bases by id. Each `_state.py` mutant
below was applied alone to a copy of the fixed tree at 692f501 and run with `-x` against
the identity, class hook, copy, copy cost and API tests on another machine (CPython 3.14.2).
11 of 13 are killed; I1 and I6 are equivalent on CPython, as explained in their rows.

| Id | Mutation | Result |
| --- | --- | --- |
| I1 | `_known` returns any entry found under the id, without checking its reference | equivalent: the callback removes a dead class's entry before CPython can reuse its memory, so the entry found under a live class's id is always that class's; the check stays as a guard on the read path |
| I2 | the weak reference callback removes nothing | killed: `tests/test_class_identity.py::test_a_class_is_freed_and_its_id_reused_safely[AtomicInt]` |
| I3 | the table holds the class itself instead of a weak reference | killed: `tests/test_class_identity.py::test_a_class_is_freed_and_its_id_reused_safely[AtomicInt]` |
| I4 | entries keyed by `hash(cls)` | killed: `tests/test_class_identity.py::test_a_subclass_of_an_unhashable_metaclass_can_be_made_and_used[AtomicInt]` |
| I5 | covered bases kept in a set of classes | killed: `tests/test_class_identity.py::test_a_subclass_of_an_unhashable_metaclass_can_be_made_and_used[AtomicInt]` |
| I6 | the reference compared with `==` instead of `is` | equivalent, for the reason given for I1 |
| I8 | names worked out at a first copy not kept | killed: `tests/test_class_hooks.py::test_under_a_base_that_skipped_the_hook_the_names_are_kept_from_the_first_copy` |
| I9 | `_collect` looks up the copied class instead of each base | killed: `tests/test_copy_slots.py::test_inherited_and_wrapped_slots_are_kept[copy-WrappedChild]` |
| I10 | a stored tuple covers only its own class | killed: `tests/test_copy_cost.py::test_making_a_class_costs_about_what_python_takes_whatever_the_depth` |
| I11 | the covered test inverted | killed: `tests/test_class_identity.py::test_classes_equal_by_name_keep_their_own_slots[copy-Same_2.z]` |
| I12 | `_known` never finds anything | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-Checked.tag]` |
| I13 | the callback clears the whole table | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-Checked.tag]` |
| I14 | `Copyable.__init_subclass__` keeps no names | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-Checked.tag]` |

I7 (the callback removing the entry only when it still holds the callback's own
reference) was run against 861a812 and survived: a reference replaced by a later `_keep`
of the same class is dropped and its callback never runs, so the condition could not be
false. 692f501 removed it.

The identity mutants were run again at 3365d13 on a third machine (CPython 3.14.6), with
the same results. The slot form fix (`_listed` reads any `__slots__` that is not an
iterator, takes each name through `str.__str__` and skips what cannot be read) was
mutated the same way at 90f1001, with `tests/test_slot_forms.py` added to the run. 8 of 9
are killed; L1 survives, as explained in its row.

| Id | Mutation | Result |
| --- | --- | --- |
| L1 | the iterator check removed | survives: Python uses up a `__slots__` iterator when it makes the class, so reading it again yields nothing; the only difference is that an iterator a base's hook put in `__slots__` afterwards would be used up, which no copy observes. The check stays so that attribute is left untouched |
| L2 | each name taken as given instead of through `str.__str__` | killed: `tests/test_slot_forms.py::test_slot_names_given_as_a_hostile_str_subclass_are_kept[copy]` |
| L3 | errors while reading `__slots__` not caught | killed: `tests/test_slot_forms.py` fails at collection (`TypeError` for the number a hook left) |
| L4 | a one-string `__slots__` iterated character by character | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-_Hidden._Hidden__tag]` |
| L5 | only tuple, list, dict, set and frozenset read again | killed: `tests/test_slot_forms.py::test_a_wrapped_slot_is_kept_whatever_iterable_listed_it[copy-deque]` |
| L6 | only `TypeError` caught | killed: `tests/test_slot_forms.py` fails at collection (`RuntimeError` from the unreadable object) |
| L7 | a listed `__dict__` taken for a slot | killed: `tests/test_copy_slots.py::test_a_declared_instance_dict_is_copied_not_shared[copy]` |
| L8 | private names mangled with the class name as is | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-_Hidden._Hidden__tag]` |
| L9 | the loop reads `__slots__` itself, not the one-string tuple | killed: `tests/test_class_hooks.py::test_a_rebuilt_or_wrapped_slot_is_kept[copy-_Hidden._Hidden__tag]` |

## After QA round 6

The class's name, MRO and namespace are now read through `type`'s own descriptors, an
`__index__` hook is bound through the `__get__` its class's MRO holds, `repr()` uses the
name Python keeps, and the linearizability test draws all eleven operations under each
policy. Each mutant below was applied alone to a copy of the fixed tree and run with `-x`
on another machine (CPython 3.14.6): N1 to N12 against the metaclass, slot descriptor,
slot form, identity, class hook, copy, copy cost, API, message and input tests; N13 and
N14 against `tests/test_linearizability.py` alone. All 14 are killed. N5 survived the
first run (every slot of that hierarchy was also listed in a `__slots__` that could be
read again) and is killed since the base class lists its slot with an iterator; N14
survived the first run (no written value left the range, so a swap never applied a
policy) and is killed since set and swap values reach past the range.

| Id | Mutation | Result |
| --- | --- | --- |
| N1 | `kind()` reads `type(value).__name__` | killed: `tests/test_metaclass.py::test_a_metaclass_name_cannot_change_an_input_error[raising]` |
| N2 | the hook's `__get__` found with `getattr` on its class | killed: `tests/test_metaclass.py::test_an_index_hook_is_bound_as_python_binds_it_whatever_its_metaclass_says` |
| N3 | `class_name()` reads `cls.__name__` | killed: `tests/test_metaclass.py` fails at collection (`RuntimeError` from the metaclass) |
| N4 | `class_name()` reads `__qualname__` | killed: `tests/test_metaclass.py::test_a_subclass_under_a_metaclass_name_is_made_shown_and_copied[copy-raising]` |
| N5 | `_declared` reads `vars(klass)` | killed: `tests/test_metaclass.py::test_a_metaclass_name_mro_or_namespace_cannot_drop_a_slot[copy-__dict__ empty]` |
| N6 | `_listed` reads `vars(klass)` | killed: `tests/test_metaclass.py::test_a_metaclass_name_mro_or_namespace_cannot_drop_a_slot[copy-__dict__ empty]` |
| N7 | `_listed` mangles with `klass.__name__` | killed: `tests/test_metaclass.py` fails at collection (`RuntimeError` from the metaclass) |
| N8 | `_collect` walks `cls.__mro__` | killed: `tests/test_metaclass.py` fails at collection (`TypeError`: the MRO is not iterable) |
| N9 | covered bases taken from `klass.__mro__` | killed: `tests/test_metaclass.py` fails at collection (`TypeError`: the MRO is not iterable) |
| N10 | `_declared` keeps another class's slot descriptor (lens e's S10) | killed: `tests/test_slot_descriptors.py::test_another_class_slot_descriptor_in_the_namespace_is_not_copied[copy]` |
| N11 | `AtomicInt.__repr__` reads `type(self).__name__` | killed: `tests/test_metaclass.py::test_a_subclass_under_a_metaclass_name_is_made_shown_and_copied[copy-raising]` |
| N12 | `BoundedAtomicInt.__repr__` reads `type(self).__name__` | killed: `tests/test_metaclass.py::test_a_subclass_under_a_metaclass_name_is_made_shown_and_copied[copy-raising]` |
| N13 | an out-of-range add stores the policy's value without checking the value it read | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[saturate]` |
| N14 | an out-of-range swap stores the policy's value without checking the value it read | killed: `tests/test_linearizability.py::test_every_recorded_history_is_linearizable[saturate]` |

## After QA round 7

`_lookup` now returns a private sentinel for a missing name, so a `__get__` set to `None`
is called as Python calls it and an `__index__` set to `None` is refused, and
`class_name()` returns a plain copy of the name Python keeps. P1 to P7 are lens e's seven
survivors of its round 7 mutation run (its N11, N12, N13, N14, N17, N21 and N24); P8 to
P12 mutate the new code. Each was applied alone to a copy of the fixed tree at a6bc329 and
run with `-x` on another machine (CPython 3.14.2) against the index lookup, class name,
slot MRO, metaclass, input, message, copy, slot and class identity tests. All 12 are
killed.

| Id | Mutation | Result |
| --- | --- | --- |
| P1 | `_lookup` walks `cls.__mro__` (lens e's N11) | killed: `tests/test_index_lookup.py::test_a_metaclass_mro_cannot_hide_an_inherited_index_hook[hiding the bases]` |
| P2 | `_lookup` walks `type.mro(cls)` (lens e's N12) | killed: `tests/test_index_lookup.py::test_the_hook_comes_from_the_order_a_metaclass_mro_made` |
| P3 | `_lookup` reads only the class's own namespace (lens e's N13) | killed: `tests/test_index_lookup.py::test_an_inherited_index_hook_is_found[one level]` |
| P4 | `_lookup` reads `vars(klass)` (lens e's N14) | killed: `tests/test_index_lookup.py::test_a_metaclass_namespace_cannot_hide_or_replace_an_index_hook[empty]` |
| P5 | `_listed` reads `getattr(klass, "__slots__", ())` (lens e's N17) | killed: `tests/test_slot_mro.py::test_an_inherited_slots_list_adds_no_attribute_to_a_copy[copy-OpenPlain]` |
| P6 | `_collect` walks `type.mro(cls)` (lens e's N21) | killed: `tests/test_slot_mro.py::test_a_slot_of_a_base_left_out_of_the_mro_is_not_copied[copy-ChildPlain]` |
| P7 | covered bases taken from `type.mro(klass)` (lens e's N24) | killed: `tests/test_slot_mro.py::test_a_base_whose_mro_leaves_a_slotted_class_out_does_not_hide_its_slots[copy-BelowPlain]` |
| P8 | a `__get__` set to `None` treated as missing (the old behaviour) | killed: `tests/test_index_lookup.py::test_a_hook_whose_class_sets_get_to_none_is_refused_as_python_refuses_it` |
| P9 | an `__index__` set to `None` not refused before binding | killed: `tests/test_index_lookup.py::test_an_index_hook_set_to_none_is_refused` |
| P10 | `class_name()` returns the kept name as is | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |
| P11 | `_lookup` returns `None` for a missing name | killed: `tests/test_metaclass.py::test_an_index_hook_is_bound_as_python_binds_it_whatever_its_metaclass_says` |
| P12 | `class_name()` returns `str()` of the kept name | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |

## After QA round 8

`_lookup` now reads each class dictionary once, the hostile class name refuses every way
to read its text, and a contract binds the hook with an owner that matters. Q11 and Q16
are lens e's two survivors of its round 8 mutation run; R1 to R8 mutate the new code and
what the new tests pin. Each was applied alone to a copy of the fixed tree at 0f334ee and
run with `-x` on another machine (CPython 3.14.2) against the index lookup, class name,
metaclass, input, message, class hook and copy tests, after an unmutated baseline run
(401 passed). All 10 are killed.

| Id | Mutation | Result |
| --- | --- | --- |
| Q11 | `class_name()` returns `"".join(name)` (lens e's) | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |
| Q16 | the hook bound as `bind(hook, value)`, without the owner (lens e's) | killed: `tests/test_index_lookup.py::test_the_hook_is_bound_with_the_value_and_its_own_type[needs]` |
| R1 | `_lookup` reads twice again (`in`, then `[]`) | killed: `tests/test_index_lookup.py::test_each_class_dict_is_read_once_so_a_changing_key_cannot_raise_key_error` |
| R2 | the owner passed is `type(hook)` | killed: `tests/test_index_lookup.py::test_the_hook_is_bound_with_the_value_and_its_own_type[needs]` |
| R3 | the owner passed is `None` | killed: `tests/test_index_lookup.py::test_the_hook_is_bound_with_the_value_and_its_own_type[needs]` |
| R4 | `_lookup` stops at a value that is not `None` instead of not the sentinel | killed: `tests/test_index_lookup.py::test_an_inherited_index_hook_is_found[one level]` |
| R5 | `class_name()` returns `name.encode().decode()` | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |
| R6 | `class_name()` returns `name.replace('', '')` | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |
| R7 | `class_name()` returns `'%s' % (name,)` | killed: `tests/test_name_subclass.py::test_a_str_subclass_name_gives_the_documented_message[raising]` |
| R8 | `_lookup` tries `[]`, and after a miss reads with `.get` and then `[]` | killed: `tests/test_index_lookup.py::test_each_class_dict_is_read_once_so_a_changing_key_cannot_raise_key_error` |
