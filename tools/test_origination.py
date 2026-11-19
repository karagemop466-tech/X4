#!/usr/bin/env python3
"""Regression tests for origination market settlement rules."""
import unittest

import csv
import os

from origination import (ROOT, edge_window, home_edge, grade_and_score, norm_cdf,
                         probability_scores, ratings_from_log, read_csv, walk_forward_rows)

OPS = os.path.join(ROOT, "data", "ops")


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


class WalkForwardTests(unittest.TestCase):
    """A line may only use what was known before its own kickoff."""

    def setUp(self):
        self.games = read_csv(os.path.join(ROOT, "data", "games-2026.csv"))

    def test_ratings_from_the_log_match_the_official_standings(self):
        from origination import team_ratings
        standings = read_csv(os.path.join(ROOT, "data", "standings-wk10-2026.csv"))
        official = team_ratings(standings, 10)
        from_log = ratings_from_log(self.games, 10)
        self.assertEqual(sorted(official), sorted(from_log))
        for team in official:
            for key in ("gp", "diff", "total", "off", "def"):
                self.assertAlmostEqual(official[team][key], from_log[team][key], places=9)

    def test_the_registered_edge_window_is_weeks_six_to_nine(self):
        # the pre-registration fitted the home edge on weeks 6-9 for Week 11
        self.assertEqual(edge_window(11), [6, 7, 8, 9])
        # and a walk-forward window never reaches the event's own week
        for week in range(4, 12):
            self.assertTrue(all(w < week for w in edge_window(week)))

    def test_no_prediction_uses_a_week_at_or_after_the_game(self):
        rows = walk_forward_rows(self.games)
        self.assertGreater(len(rows), 50)
        for r in rows:
            self.assertTrue(all(w < r["week"] for w in edge_window(r["week"])))

    def test_the_forward_week_lines_are_unchanged(self):
        # the pre-registered Week 11 numbers, committed before this change
        fair = read_csv(os.path.join(OPS, "fair_lines.csv"))
        rows = {r["event_id"]: r for r in fair if r["week"] == "11"}
        self.assertEqual(rows["401873066"]["fair_side_home"], "5.2")
        self.assertEqual(rows["401873066"]["fair_total"], "48.2")
        self.assertEqual(rows["401873066"]["fair_ml_home_pct"], "64.87")
        self.assertEqual(rows["401873066"]["home_edge"], "-0.39")
        self.assertEqual(rows["401873066"]["sigma"], "13.6")
        self.assertEqual(rows["401873070"]["fair_side_home"], "12.2")
        self.assertEqual(rows["401873070"]["fair_total"], "47.2")
        self.assertEqual(rows["401873070"]["fair_ml_home_pct"], "81.59")


class ProbabilityStoreTests(unittest.TestCase):
    """Every originated market carries a probability and the inputs behind it."""

    def setUp(self):
        with open(os.path.join(OPS, "model_outputs.csv"), newline="", encoding="utf-8") as fh:
            self.rows = list(csv.DictReader(fh))

    def test_every_market_has_a_probability_and_its_inputs(self):
        self.assertEqual(len(self.rows), 30)
        for r in self.rows:
            self.assertTrue(r["probability"], r)
            self.assertTrue(r["event"], r)
            self.assertTrue(r["sigma"], r)
            self.assertTrue(r["sigma_n"], r)
            self.assertTrue(r["sigma_window"], r)
            self.assertTrue(r["official_url"], r)
            self.assertTrue(r["input_source"], r)
            self.assertTrue(r["ratings_through_week"], r)

    def test_the_probability_matches_its_stated_formula(self):
        for r in self.rows:
            if not r["probability"] or not r["mu"]:
                continue
            mu, sigma = float(r["mu"]), float(r["sigma"])
            expected = norm_cdf(mu / sigma)
            self.assertAlmostEqual(float(r["probability"]), expected, places=3)

    def test_the_moneyline_probability_is_the_registered_one(self):
        # the registered Week 11 moneyline probability must not move
        rows = {r["event_id"]: r for r in self.rows
                if r["week"] == "11" and r["market"] == "moneyline"}
        self.assertAlmostEqual(float(rows["401873066"]["probability"]), 0.6487, places=4)
        self.assertAlmostEqual(float(rows["401873070"]["probability"]), 0.8159, places=4)

    def test_the_market_benchmark_says_which_price_it_is(self):
        # a close that was really the last captured price is a proxy, and the
        # label has to say so rather than call it a closing price
        rows = {r["market"]: r for r in self.rows if r["week"] == "11"}
        for r in rows.values():
            if r["market_probability"]:
                self.assertNotIn("closing price", r["market_probability_basis"],
                                 "the benchmark basis must name the price it used")

    def test_a_total_has_no_market_benchmark_and_says_so(self):
        for r in self.rows:
            if r["market"] != "total":
                continue
            self.assertEqual(r["market_probability"], "")
            self.assertIn("no probability", r["market_probability_basis"])


class ProperScoreTests(unittest.TestCase):
    """A probability is scored against a market forecast of the same event."""

    def setUp(self):
        self.dispersion = {
            "sigma_margin_model": 12.31, "sigma_total_model": 13.40,
            "sigma_margin_league": 13.52, "sigma_total_league": 14.18,
            "n": 102, "window": "weeks 4-10 of the official game log", "league_n": 150,
            "method": "test",
        }

    def test_a_push_is_not_scored(self):
        fmd = [{"event_id": "e1", "week": "10", "away": "CLE", "home": "NO", "market": "side",
                "fair": "0.0", "market_close": "-3", "close_kind": "close", "settled": "1"}]
        results = {(10, "CLE", "NO"): {"margin": 3, "total": 45, "home_pts": 24, "away_pts": 21,
                                       "url": "https://www.nfl.com/games/test"}}
        rows = probability_scores(fmd, results, [], self.dispersion)
        self.assertEqual(rows[0]["n"], 0)

    def _score(self, fair, home_margin):
        fmd = [{"event_id": "e1", "week": "10", "away": "CLE", "home": "NO", "market": "side",
                "fair": str(fair), "market_close": "-3", "close_kind": "close", "settled": "1"}]
        results = {(10, "CLE", "NO"): {"margin": home_margin, "total": 45,
                                       "home_pts": 28, "away_pts": 18,
                                       "url": "https://www.nfl.com/games/test"}}
        snaps = [{"event_id": "e1", "market": "moneyline", "selection": "home", "close_ml": "-200"},
                 {"event_id": "e1", "market": "moneyline", "selection": "away", "close_ml": "+180"}]
        rows = probability_scores(fmd, results, snaps, self.dispersion)
        return [r for r in rows if r["market"] == "side"][0]

    def test_the_benchmark_label_is_exact_about_the_price_it_used(self):
        fmd = [{"event_id": "e1", "week": "10", "away": "CLE", "home": "NO", "market": "moneyline",
                "fair": "60.0", "market_close": "-200", "close_kind": "current_as_close", "settled": "1"}]
        results = {(10, "CLE", "NO"): {"margin": 10, "total": 45, "home_pts": 28, "away_pts": 18,
                                       "url": "https://www.nfl.com/games/test"}}
        snaps = [{"event_id": "e1", "market": "moneyline", "selection": "home",
                  "close_ml": "-200", "close_kind": "current_as_close"},
                 {"event_id": "e1", "market": "moneyline", "selection": "away",
                  "close_ml": "+170", "close_kind": "current_as_close"}]
        rows = probability_scores(fmd, results, snaps, self.dispersion)
        ml = [r for r in rows if r["market"] == "moneyline"][0]
        self.assertIn("not a true close", ml["benchmark"])
        self.assertEqual(ml["benchmark_rows"], "current_as_close: 1")

    def test_a_true_close_is_named_as_one(self):
        fmd = [{"event_id": "e1", "week": "10", "away": "CLE", "home": "NO", "market": "moneyline",
                "fair": "60.0", "market_close": "-200", "close_kind": "close", "settled": "1"}]
        results = {(10, "CLE", "NO"): {"margin": 10, "total": 45, "home_pts": 28, "away_pts": 18,
                                       "url": "https://www.nfl.com/games/test"}}
        snaps = [{"event_id": "e1", "market": "moneyline", "selection": "home",
                  "close_ml": "-200", "close_kind": "close"},
                 {"event_id": "e1", "market": "moneyline", "selection": "away",
                  "close_ml": "+170", "close_kind": "close"}]
        rows = probability_scores(fmd, results, snaps, self.dispersion)
        ml = [r for r in rows if r["market"] == "moneyline"][0]
        self.assertIn("a true closing price", ml["benchmark"])
        self.assertEqual(ml["benchmark_rows"], "close: 1")

    def test_both_forecasts_are_about_the_same_event(self):
        side = self._score(0.0, 10)
        self.assertEqual(side["n"], 1)
        self.assertTrue(side["model_brier"])
        self.assertTrue(side["market_brier"])
        for key in ("model_brier", "market_brier"):
            self.assertGreaterEqual(float(side[key]), 0.0)
            self.assertLessEqual(float(side[key]), 1.0)
        # the market forecast comes from the captured price, and is not the model's line
        self.assertIn("de-vigged", side["benchmark"])

    def test_a_closer_model_scores_better_than_the_market(self):
        # the market implies about +5.2 points; a model that expects +10 is closer
        # to the 10-point margin that actually happened
        side = self._score(10.0, 10)
        self.assertLess(float(side["model_brier"]), float(side["market_brier"]))
        self.assertGreater(float(side["skill"]), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
