import copy
import json
import math
import struct
import unittest

from paperprobe.generation import generate_candidates


def opportunity(threshold=16, *, variable="n", value_type="integer", kind="boundary", **extra):
    return {
        "opportunity_id": "op-1", "paper_id": "paper-1", "scope_status": "unknown",
        "paper_evidence": [{"quote": "A supported mechanism"}], "scope_constraints": [],
        "condition": {"condition_id": "cond-1", "variable": variable, "threshold": threshold,
                      "value_type": value_type, "kind": kind, "operator": "<",
                      "expression": f"{variable} < {threshold}",
                      "evidence": {"path": "target.py", "line_start": 4, "line_end": 4,
                                   "quote": f"{variable} < {threshold}", "sha256": "example"},
                      "input_binding": "unconfirmed"}, **extra,
    }


class GenerationTests(unittest.TestCase):
    def test_integer_triplet_is_one_candidate(self):
        candidate = generate_candidates([opportunity()])[0]
        self.assertEqual(candidate["inputs"], [{"n": 15}, {"n": 16}, {"n": 17}])
        self.assertEqual(candidate["strategy"], "boundary")
        self.assertEqual(candidate["scope_status"], "unknown")
        self.assertEqual(candidate["oracle"]["type"], "reachability")
        self.assertEqual(candidate["oracle"]["status"], "proposed")
        self.assertEqual(candidate["oracle"]["semantic_validation_status"], "unknown")
        self.assertEqual(candidate["backend"], "deterministic_heuristic")

    def test_negative_float_uses_representable_neighbors(self):
        candidate = generate_candidates([opportunity(-2.5, value_type="float")])[0]
        values = [item["n"] for item in candidate["inputs"]]
        self.assertEqual(values, [math.nextafter(-2.5, -math.inf), -2.5, math.nextafter(-2.5, math.inf)])
        self.assertTrue(all(type(value) is float for value in values))

    def test_float_variable_with_integer_literal_keeps_float_type(self):
        candidate = generate_candidates([opportunity(16, value_type="float")])[0]
        self.assertTrue(all(type(item["n"]) is float for item in candidate["inputs"]))
        self.assertEqual(candidate["inputs"][1], {"n": 16.0})

    def test_integer_variable_with_noninteger_threshold_is_not_given_floats(self):
        candidate = generate_candidates([opportunity(3.5)])[0]
        self.assertEqual(candidate["inputs"], [{"n": 3}, {"n": 4}])

    def test_float32_neighbors_do_not_collapse_after_conversion(self):
        item = opportunity(32.0, value_type="float")
        item["condition"]["numeric_format"] = "float32"
        values = [sample["n"] for sample in generate_candidates([item])[0]["inputs"]]
        converted = [struct.unpack("!f", struct.pack("!f", value))[0] for value in values]
        self.assertEqual(values, converted)
        self.assertEqual(len(set(converted)), 3)
        self.assertLess(converted[0], 32.0)
        self.assertGreater(converted[-1], 32.0)

    def test_boolean_configuration_has_two_boolean_probes(self):
        candidate = generate_candidates([opportunity(True, variable="config.enabled", value_type="boolean", kind="configuration")])[0]
        self.assertEqual(candidate["inputs"], [{"config.enabled": False}, {"config.enabled": True}])
        self.assertTrue(all(type(item["config.enabled"]) is bool for item in candidate["inputs"]))

    def test_unknown_truthiness_does_not_invent_boolean_type(self):
        candidate = generate_candidates([opportunity(True, variable="items", value_type="unknown", kind="configuration")])[0]
        self.assertEqual(candidate["inputs"], [])

    def test_unknown_truthiness_can_use_explicit_boolean_domain(self):
        item = opportunity(True, variable="enabled", value_type="unknown", kind="configuration",
                           scope_constraints=[{"variable": "enabled", "type": "boolean", "source": "paper", "evidence_id": "p1"}])
        self.assertEqual(generate_candidates([item])[0]["inputs"], [{"enabled": False}, {"enabled": True}])

    def test_configuration_values_come_from_known_enumeration(self):
        item = opportunity("fast", variable="config.mode", value_type="string", kind="configuration",
                           scope_constraints=[{"variable": "config.mode", "type": "string", "enum": ["fast", "safe"], "evidence_id": "p1"}])
        self.assertEqual(generate_candidates([item])[0]["inputs"], [{"config.mode": "fast"}, {"config.mode": "safe"}])
        item["scope_constraints"] = []
        self.assertEqual(generate_candidates([item])[0]["inputs"], [])

    def test_domain_violating_probe_is_withheld(self):
        item = opportunity(scope_status="in_scope", scope_constraints=[{"variable": "n", "minimum": 15, "maximum": 16, "type": "integer", "source": "paper", "evidence_id": "p1"}])
        candidate = generate_candidates([item])[0]
        self.assertEqual(candidate["inputs"], [{"n": 15}, {"n": 16}])
        self.assertEqual(candidate["withheld_inputs"][0]["inputs"], {"n": 17})
        self.assertIn("range", candidate["withheld_inputs"][0]["reason"])

    def test_scope_can_block_all_inputs_and_candidate_is_preserved(self):
        for scope in ("out_of_scope", "abstain"):
            candidate = generate_candidates([opportunity(scope_status=scope)])[0]
            self.assertEqual(candidate["inputs"], [])
            self.assertEqual(len(candidate["withheld_inputs"]), 3)

    def test_no_crossing_in_valid_domain_is_not_claimed(self):
        item = opportunity(scope_constraints=[{"variable": "n", "minimum": 16, "maximum": 17}])
        candidate = generate_candidates([item])[0]
        self.assertEqual(candidate["inputs"], [{"n": 16}, {"n": 17}])
        self.assertTrue(any("prevent crossing" in text for text in candidate["limitations"]))

    def test_exclusive_bound_and_operator_constraint(self):
        item = opportunity(scope_constraints=[{"variable": "n", "minimum": 15, "minimum_inclusive": False}, {"variable": "n", "operator": "<", "value": 17}])
        self.assertEqual(generate_candidates([item])[0]["inputs"], [{"n": 16}])

    def test_malformed_domain_fails_closed(self):
        for constraint in ({"variable": "n", "minimum": "low"}, {"variable": "n", "enum": "1,2,3"},
                           {"variable": "n", "minimum": 15, "minimum_inclusive": "false"},
                           {"variable": "n", "operator": "!=", "value": math.inf}):
            candidate = generate_candidates([opportunity(scope_constraints=[constraint])])[0]
            self.assertEqual(candidate["inputs"], [])
            self.assertEqual(len(candidate["withheld_inputs"]), 3)

    def test_derived_expression_requires_mapping_instead_of_fake_input(self):
        item = opportunity(8, variable="len(items)")
        item["condition"]["input_binding"] = "derived_expression"
        candidate = generate_candidates([item])[0]
        self.assertEqual(candidate["inputs"], [])
        self.assertEqual(candidate["strategy"], "requires_input_mapping")

    def test_state_requires_a_legal_sequence(self):
        candidate = generate_candidates([opportunity("ready", variable="session.state", value_type="string", kind="state")])[0]
        self.assertEqual(candidate["inputs"], [])
        self.assertEqual(candidate["strategy"], "state_transition")

    def test_oracle_is_only_proposed_even_if_input_claims_validated(self):
        item = opportunity(proposed_oracle={"type": "invariant", "status": "validated", "relation": "Output equals the independently reviewed reference", "evidence": [{"quote": "Explicit invariant"}]})
        candidate = generate_candidates([item])[0]
        self.assertEqual(candidate["oracle"]["type"], "invariant")
        self.assertEqual(candidate["oracle"]["status"], "proposed")
        self.assertEqual(candidate["oracle"]["semantic_validation_status"], "unknown")

    def test_code_only_does_not_leak_paper_domain_or_property(self):
        item = opportunity(scope_status="in_scope", scope_constraints=[{"variable": "n", "minimum": 16, "source": "paper"}],
                           proposed_oracle={"type": "invariant", "relation": "Paper property", "source": "paper", "evidence": [{"quote": "Paper"}]})
        candidate = generate_candidates([item], method="code_only")[0]
        self.assertEqual(candidate["inputs"], [{"n": 15}, {"n": 16}, {"n": 17}])
        self.assertEqual(candidate["paper_evidence"], [])
        self.assertEqual(candidate["scope_status"], "unknown")
        self.assertEqual(candidate["oracle"]["type"], "reachability")
        item["scope_constraints"][0]["source"] = "code"
        self.assertEqual(generate_candidates([item], method="code_only")[0]["inputs"], [{"n": 16}, {"n": 17}])

    def test_activation_preconditions_and_original_evidence_survive(self):
        item = opportunity()
        item["condition"]["activation_preconditions"] = ["enabled is true"]
        candidate = generate_candidates([item])[0]
        self.assertIn("enabled is true", candidate["preconditions"])
        self.assertEqual(candidate["target_condition"], item["condition"])
        self.assertEqual(candidate["code_evidence"], item["condition"]["evidence"])

    def test_large_float_infinity_probes_are_withheld(self):
        item = opportunity(float.fromhex("0x1.fffffffffffffp+1023"), value_type="float")
        candidate = generate_candidates([item])[0]
        self.assertEqual(len(candidate["inputs"]), 2)
        self.assertTrue(all(math.isfinite(sample["n"]) for sample in candidate["inputs"]))
        json.dumps(candidate, allow_nan=False)

    def test_determinism_input_immutability_and_limits(self):
        items = [opportunity(), opportunity(32, opportunity_id="op-2")]
        original = copy.deepcopy(items)
        self.assertEqual(generate_candidates(items), generate_candidates(items))
        self.assertEqual(items, original)
        self.assertEqual(len(generate_candidates(items, max_candidates=1)), 1)
        self.assertEqual(generate_candidates(items, max_candidates=0), [])
        with self.assertRaises(ValueError):
            generate_candidates(items, max_candidates=-1)


if __name__ == "__main__":
    unittest.main()
