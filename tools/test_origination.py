#!/usr/bin/env python3
"""Regression tests for origination market settlement rules."""
import unittest

from origination import grade_and_score


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
