import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import availability, build, security_roi, tco  # noqa: E402


def load(name):
    return json.loads((ROOT / "models" / name).read_text())


class AvailabilityTests(unittest.TestCase):
    def test_serial_dependencies_multiply(self):
        comps = [availability.Component("a", 99.99), availability.Component("b", 99.95)]
        self.assertAlmostEqual(availability.serial(comps), 0.9999 * 0.9995)

    def test_redundancy_multiplies_failure_probabilities(self):
        self.assertAlmostEqual(availability.redundant([0.999, 0.999]), 1 - 0.001 * 0.001)

    def test_one_region_cannot_reach_four_nines_but_two_can(self):
        scenarios = {s["name"]: availability.evaluate(s) for s in load("availability.json")["scenarios"]}
        self.assertFalse(scenarios["Financial portal, one region (Case 4)"]["meets"])
        self.assertTrue(scenarios["Financial portal, two regions (Case 4)"]["meets"])

    def test_formatting_never_rounds_up_to_100_percent(self):
        self.assertEqual(availability.fmt_pct(0.99999995), "99.999995%")
        self.assertEqual(availability.fmt_pct(0.9999999999), "99.999999%")
        self.assertEqual(availability.fmt_pct(0.9993), "99.930%")

    def test_downtime_conversion(self):
        self.assertAlmostEqual(availability.downtime_minutes_per_year(0.999), 525.96, places=1)


class TcoTests(unittest.TestCase):
    def setUp(self):
        self.inp = load("medtech-tco.json")

    def test_one_time_and_dual_running_costs_fall_away(self):
        y3 = tco.cloud_year(self.inp, 3)
        self.assertEqual(y3["Migration (one-time: partners, training, tooling)"], 0)
        self.assertEqual(y3["Dual running (on-prem not yet retired, excl. staff)"], 0)
        self.assertGreater(tco.cloud_year(self.inp, 1)["Migration (one-time: partners, training, tooling)"], 0)

    def test_steady_state_meets_target_even_if_three_years_does_not(self):
        r = tco.run(self.inp)
        self.assertGreaterEqual(r["steady_state_saving_pct"], self.inp["target_saving_pct"])
        self.assertLess(r["cumulative_saving"][0], 0)  # year 1 always costs more: dual running + migration

    def test_staff_assumption_moves_the_answer_the_right_way(self):
        (_, more_staff, fewer_staff), *_ = tco.sensitivity(self.inp, self.inp["sensitivity"][:1])
        self.assertLess(more_staff, fewer_staff)

    def test_sensitivity_does_not_mutate_inputs(self):
        before = json.dumps(self.inp, sort_keys=True)
        tco.sensitivity(self.inp, self.inp["sensitivity"])
        self.assertEqual(before, json.dumps(self.inp, sort_keys=True))


class RosiTests(unittest.TestCase):
    def setUp(self):
        self.inp = load("medsecure-rosi.json")

    def test_break_even_probability_gives_zero_return(self):
        self.assertAlmostEqual(security_roi.rosi(self.inp, aro=security_roi.breakeven_aro(self.inp)), 0, places=9)

    def test_rare_breaches_make_the_program_a_loss(self):
        self.assertLess(security_roi.rosi(self.inp, aro=0.02, effectiveness=0.3), 0)


class BuildTests(unittest.TestCase):
    def test_docs_are_up_to_date_with_the_models(self):
        self.assertEqual(build.main(check=True), 0)

    def test_render_is_idempotent(self):
        for md in ROOT.rglob("*.md"):
            text = md.read_text()
            if "BEGIN GENERATED" in text:
                once = build.render(text)
                self.assertEqual(once, build.render(once), md)


if __name__ == "__main__":
    unittest.main()
