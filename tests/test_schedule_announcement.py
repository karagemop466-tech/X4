"""Offline regression checks for the dated NFL schedule notice on the fixture page."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "brief-register.html"
ANNOUNCEMENT_URL = (
    "https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-"
    "to-be-released-thursday--may-14"
)
LIVE_SCHEDULE_URL = "https://www.nfl.com/schedules/2026/"
WEEK11_SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"


class ScheduleAnnouncementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        marker = '<div class="card schedule-announcement" id="schedule-announcement">'
        start = cls.html.find(marker)
        if start < 0:
            raise AssertionError("the generated fixture page has no schedule announcement card")
        end = cls.html.find("</div>", start)
        if end < 0:
            raise AssertionError("the schedule announcement card is not closed")
        cls.card = cls.html[start : end + len("</div>")]
        cls.card_start = start

    def test_announcement_date_and_release_time_are_both_explicit(self):
        self.assertIn("Announcement published May 8, 2026", self.card)
        self.assertIn("Thursday, May 14 at 8 p.m. ET", self.card)
        self.assertIn(f'href="{ANNOUNCEMENT_URL}"', self.card)

    def test_live_and_weekly_schedule_sources_are_separate_from_the_announcement(self):
        self.assertIn(f'href="{LIVE_SCHEDULE_URL}"', self.card)
        self.assertIn(f'href="{WEEK11_SCHEDULE_URL}"', self.card)
        self.assertIn("Both pages were read on 2026-11-19", self.card)
        self.assertIn("not inferred from the older announcement", self.card)

    def test_announcement_sits_with_the_current_fixture_context(self):
        context = self.html.index("R2 &middot; Fixture context")
        fixture_table = self.html.index("<th>Date</th>", self.card_start)
        self.assertLess(context, self.card_start)
        self.assertLess(self.card_start, fixture_table)
        self.assertIn("game-centre pages", self.card)


if __name__ == "__main__":
    unittest.main()
