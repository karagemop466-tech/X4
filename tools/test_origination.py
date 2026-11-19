#!/usr/bin/env python3
"""Regression tests for origination market settlement rules and probability outputs."""
import unittest

from origination import (brier_rows, brier_summary, devig_pair, event_probability,
                         fair_market_difference, grade_and_score)


class SpreadSettlementTests(unittest.TestCase):
    def grade_side(self, fair, home_line, home_margin, bet_prices):
        event_id = "test-event"
        fmd = [{
            "event_id": event_id,
            "week": "9",
            "away": "CLE",
            "home": "NO",
            "market": "side",
            "fair": str(fair),
            "market_close": str(home_line),
            "close_kind": "close",
        }]
        results = {(9, "CLE", "NO"): {"margin": home_margin, "total": 45,
                                        "home_pts": 23, "away_pts": 22,
                                        "url": "https://www.nfl.com/games/test"}}
        snapshots = [{
            "event_id": event_id,
            "market": "side",
            "selection": selection,
            "close_price": price,
            "open_price": price,
        } for selection, price in bet_prices.items()]
        settled, _, _, _, _ = grade_and_score(fmd, results, snapshots)
        self.assertEqual(len(settled), 1)
        return settled[0]

    def test_away_plus_points_wins_despite_losing_straight_up(self):
        # CLE lost 22-23, but covered NO -4.5 (CLE +4.5). A prior settlement
        # incorrectly used the straight-up winner and recorded this as a loss.
        row = self.grade_side(
            fair=-0.3,
            home_line=-4.5,
            home_margin=1,
            bet_prices={"away": "-105", "home": "-115"},
        )
        self.assertEqual(row["bet"], "away")
        self.assertEqual(row["outcome"], "won")
        self.assertAlmostEqual(row["pnl"], 100.0 / 105.0)

    def test_home_side_must_cover_the_spread(self):
        row = self.grade_side(
            fair=6.0,
            home_line=-4.5,
            home_margin=7,
            bet_prices={"home": "-110", "away": "-110"},
        )
        self.assertEqual(row["bet"], "home")
        self.assertEqual(row["outcome"], "won")

    def test_exact_spread_push_is_not_a_win_or_loss(self):
        row = self.grade_side(
            fair=5.0,
            home_line=-3,
            home_margin=3,
            bet_prices={"home": "-110", "away": "-110"},
        )
        self.assertEqual(row["bet"], "home")
        self.assertEqual(row["outcome"], "push")
        self.assertEqual(row["pnl"], 0.0)


class ProbabilityOutputTests(unittest.TestCase):
    """T76 (E5): every model output is a probability plus its inputs."""

    def test_side_probability_is_half_at_the_fair_line(self):
        # P(home covers its own fair line) must be exactly 0.5
        self.assertAlmostEqual(event_probability("side", 3.0, 13.6, -3.0), 0.5, places=6)

    def test_side_probability_moves_monotonically_with_the_line(self):
        # a bigger home handicap makes home_covers less likely
        lo = event_probability("side", 0.0, 13.6, -10.0)
        hi = event_probability("side", 0.0, 13.6, 10.0)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_total_probability_is_half_neighbourhood_at_the_fair_number(self):
        p = event_probability("total", 45.0, "", 45.0)
        self.assertGreater(p, 0.3)
        self.assertLess(p, 0.7)

    def test_total_probability_falls_as_the_line_rises(self):
        self.assertGreater(event_probability("total", 45.0, "", 40.0),
                           event_probability("total", 45.0, "", 50.0))

    def test_moneyline_probability_at_zero_margin(self):
        self.assertAlmostEqual(event_probability("moneyline", 0.0, 13.6, None), 0.5, places=6)

    def test_missing_inputs_return_none_not_a_guess(self):
        self.assertIsNone(event_probability("side", 1.0, "", -3.0))
        self.assertIsNone(event_probability("side", "", 13.6, -3.0))
        self.assertIsNone(event_probability("total", 45.0, "", ""))
        self.assertIsNone(event_probability("moneyline", 1.0, 0.0, None))

    def test_devig_pair_removes_the_vig(self):
        self.assertAlmostEqual(devig_pair("-110", "-110"), 0.5, places=6)
        self.assertGreater(devig_pair("-150", "+130"), 0.5)
        self.assertIsNone(devig_pair("", "-110"))

    def test_fmd_rows_store_probability_and_raw_result(self):
        markets = [{"event_id": "E1", "week": "9", "away": "CLE", "home": "NO",
                    "market": "side", "book": "DraftKings", "fair_home": "3.0"}]
        snapshots = [{"event_id": "E1", "market": "side", "selection": "home",
                      "open_line": "-3", "close_line": "-4.5", "close_kind": "close",
                      "retrieved_utc": "2026-11-14T00:00:00Z",
                      "source_url": "https://example.invalid/synthetic"},
                     {"event_id": "E1", "market": "side", "selection": "away",
                      "open_line": "+3", "close_line": "+4.5", "close_kind": "close",
                      "retrieved_utc": "2026-11-14T00:00:00Z",
                      "source_url": "https://example.invalid/synthetic"}]
        results = {(9, "CLE", "NO"): {"margin": 1, "total": 45, "home_pts": 23,
                                      "away_pts": 22, "url": "https://example.invalid/synthetic"}}
        fair_by_event = {"E1": {"fair_side_home": "3.0", "fair_total": "45.0", "sigma": "13.6"}}
        rows = fair_market_difference(markets, snapshots, results, fair_by_event)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["prob_dist"], "normal_margin")
        self.assertEqual(r["prob_event"], "home_covers")
        self.assertEqual(r["prob_mu"], "3.0")
        self.assertEqual(r["prob_sigma"], "13.6")
        # at home -3 the fair margin +3 implies exactly 50%
        self.assertEqual(r["prob_event_open_pct"], "50.00")
        # home -4.5 => Phi((3 - 4.5) / 13.6) < 50%
        self.assertLess(float(r["prob_event_close_pct"]), 50.0)
        self.assertEqual(r["result_margin"], "1")
        self.assertEqual(r["result_total"], "45")

    def test_brier_model_edge_scores_positive_skill(self):
        # model 0.9 on events that happen 90% of the time; market 0.5
        fmd = []
        results = {}
        snapshots = []
        for i in range(10):
            y = 1 if i < 9 else 0
            ev = "B%d" % i
            home = "T%d" % i
            fmd.append({"event_id": ev, "week": "9", "away": "CLE", "home": home,
                        "market": "moneyline", "fair": "90.00%", "market_close": "-110",
                        "close_kind": "close", "prob_event_close_pct": "90.00",
                        "settled": "1",
                        "result": "home" if y else "away", "result_margin": "1" if y else "-1",
                        "result_total": "45"})
            results[(9, "CLE", home)] = {"margin": 1 if y else -1, "total": 45,
                                         "home_pts": 23, "away_pts": 22,
                                         "url": "https://example.invalid/synthetic"}
            snapshots.append({"event_id": ev, "market": "moneyline", "selection": "home",
                              "close_ml": "-110"})
            snapshots.append({"event_id": ev, "market": "moneyline", "selection": "away",
                              "close_ml": "-110"})
        rows = brier_rows(fmd, results, snapshots)
        self.assertEqual(len(rows), 10)
        s = brier_summary(rows)
        self.assertEqual(s["moneyline"]["n"], 10)
        self.assertGreater(s["moneyline"]["skill"], 0.0)

    def test_rows_without_a_probability_are_excluded_never_filled(self):
        fmd = [{"event_id": "X1", "week": "9", "away": "CLE", "home": "NO",
                "market": "side", "market_close": "-4.5", "close_kind": "close",
                "settled": "1", "result": "home", "result_margin": "7", "result_total": "45"}]
        results = {(9, "CLE", "NO"): {"margin": 7, "total": 45, "home_pts": 26,
                                      "away_pts": 19, "url": "https://example.invalid/synthetic"}}
        self.assertEqual(brier_rows(fmd, results, []), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
