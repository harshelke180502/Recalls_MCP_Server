import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recalls_server import limits, tools  # noqa: E402
from tests import fixture  # noqa: E402


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = os.path.join(cls.tmp.name, "recalls.db")
        fixture.build(cls.path)
        os.environ["RECALLS_DB"] = cls.path

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("RECALLS_DB", None)
        cls.tmp.cleanup()

    # search_recalls: keyword in title (not a README question).
    def test_search_matches_title(self):
        out = tools.search_recalls("Helmets")
        self.assertEqual([r["recall_number"] for r in out["results"]], ["25202"])

    # search_recalls query="Amazon" hits title too — why Q2 must use sold_at, not query.
    def test_search_matches_where_sold(self):
        out = tools.search_recalls("Amazon")
        self.assertEqual(out["total"], 4)

    # search_recalls: keyword in hazard (not a README question).
    def test_search_matches_hazard(self):
        out = tools.search_recalls("fire")
        self.assertEqual(out["total"], 4)

    # search_recalls default sort=date (Q3 variation: omit sort → still newest first).
    def test_search_is_newest_first(self):
        out = tools.search_recalls("")
        dates = [r["recall_date"] for r in out["results"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    # Q1-style year filter on search (Q1 itself uses count_recalls).
    def test_year_filter(self):
        self.assertEqual(tools.search_recalls(year=2026)["total"], 9)
        self.assertEqual(tools.search_recalls(year=2025)["total"], 2)

    # Q1: count_recalls(year) matches search total — announcement count, not units.
    def test_count_matches_search_total(self):
        for query, year in (("", None), ("fire", None), ("Amazon", 2026), ("", 2025)):
            self.assertEqual(tools.count_recalls(query, year)["count"], tools.search_recalls(query, year)["total"])

    # search_recalls paging (not a README question).
    def test_paging_walks_every_row(self):
        seen, cursor = [], 0
        while True:
            out = tools.search_recalls("", limit=3, cursor=cursor)
            seen += [r["recall_number"] for r in out["results"]]
            if "next_cursor" not in out:
                break
            cursor = out["next_cursor"]
        self.assertEqual(len(seen), 11)
        self.assertEqual(len(set(seen)), 11)

    # search_recalls limit cap (not a README question).
    def test_limit_is_clamped(self):
        self.assertEqual(limits.clamp_limit(500), limits.MAX_LIMIT)
        self.assertEqual(limits.clamp_limit(0), limits.DEFAULT_LIMIT)

    # Q5: get_recall accepts 26-101 and 26101.
    def test_get_recall_accepts_dash(self):
        self.assertEqual(tools.get_recall("26-101")["title"], tools.get_recall("26101")["title"])

    # get_recall missing number (not a README question).
    def test_get_recall_missing(self):
        self.assertFalse(tools.get_recall("99-999")["found"])

    # Q5: add_note then get_recall shows the note.
    def test_add_note_shows_on_get_recall(self):
        saved = tools.add_note("26102", "Checked the catalogue, nothing listed.", author="agent:test")
        self.assertTrue(saved["saved"])
        notes = tools.get_recall("26102")["notes"]
        self.assertEqual(notes[-1]["body"], "Checked the catalogue, nothing listed.")
        self.assertEqual(notes[-1]["author"], "agent:test")

    # Q5: add_note("26-102") then get_recall("26102") / "26-102" both see the note.
    def test_add_note_normalizes_dashed_number(self):
        saved = tools.add_note("26-103", "Legal is reviewing our listings.")
        self.assertTrue(saved["saved"])
        self.assertEqual(saved["recall_number"], "26103")
        self.assertEqual(tools.get_recall("26-103")["notes"][-1]["body"], "Legal is reviewing our listings.")
        self.assertEqual(tools.get_recall("26103")["notes"][-1]["body"], "Legal is reviewing our listings.")

    # Q5: "Recall 26-104" strips to 26104 like get_recall.
    def test_add_note_normalizes_prefixed_number(self):
        saved = tools.add_note("Recall 26-104", "Checked listings.")
        self.assertTrue(saved["saved"])
        self.assertEqual(saved["recall_number"], "26104")
        self.assertEqual(tools.get_recall("26104")["notes"][-1]["body"], "Checked listings.")

    # Q5 variation: empty note is rejected.
    def test_add_note_rejects_empty(self):
        self.assertFalse(tools.add_note("26102", "   ")["saved"])

    # Last N days with no retailer (not Q2 — Q2 also needs sold_at).
    def test_recent_recalls_window(self):
        out = tools.recent_recalls(30, today=dt.date(2026, 3, 25))
        self.assertEqual([r["recall_number"] for r in out["results"]], ["26108", "26107", "26106", "26105"])

    # sold_at_recalls is unused: Q2 is covered by recent_recalls(days, sold_at).
    # def test_sold_at_recalls_q2_last_30_days_amazon(self):
    #     out = tools.sold_at_recalls("Amazon", days=30, today=dt.date(2026, 3, 25))
    #     self.assertEqual([r["recall_number"] for r in out["results"]], ["26105"])
    #     self.assertEqual(out["count"], 1)
    #
    # def test_sold_at_recalls_requires_retailer(self):
    #     out = tools.sold_at_recalls("  ")
    #     self.assertEqual(out["count"], 0)
    #     self.assertIn("sold_at", out["error"])

    # Q2: last 30 days sold on Amazon — one recent_recalls(days, sold_at).
    def test_recent_recalls_sold_at_amazon_last_30_days(self):
        out = tools.recent_recalls(30, today=dt.date(2026, 3, 25), sold_at="Amazon")
        self.assertEqual([r["recall_number"] for r in out["results"]], ["26105"])
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["sold_at"], "Amazon")
        self.assertEqual(out["days"], 30)

    # Q2 variation: last X days (7, not 30) sold on Amazon.
    def test_recent_recalls_sold_at_respects_day_window(self):
        out = tools.recent_recalls(7, today=dt.date(2026, 3, 25), sold_at="Amazon")
        self.assertEqual(out["results"], [])
        self.assertEqual(out["days"], 7)

    # Q2/Q4: sold_at matches the sold_at column only, not "Amazon" in the title.
    def test_sold_at_ignores_amazon_in_title(self):
        out = tools.search_recalls(sold_at="Amazon")
        numbers = [r["recall_number"] for r in out["results"]]
        self.assertEqual(out["total"], 3)
        self.assertNotIn("26100", numbers)
        self.assertEqual(tools.count_recalls(sold_at="Amazon")["count"], 3)

    # Q4: count sold at Walmart matches search sold_at total (announcements, not units).
    def test_count_sold_at_matches_search(self):
        self.assertEqual(
            tools.count_recalls(sold_at="Walmart")["count"],
            tools.search_recalls(sold_at="Walmart")["total"],
        )

    # Q2 variation: days clamped to 1–365 (0→30, 999→365).
    def test_recent_days_are_clamped(self):
        out = tools.recent_recalls(0, today=dt.date(2026, 3, 25))
        self.assertEqual(out["days"], 30)
        out = tools.recent_recalls(999, today=dt.date(2026, 3, 25))
        self.assertEqual(out["days"], 365)

    # Q3: most units in a year — search_recalls(year, sort=units, limit=1). Fixture 2026 max is 26102 (15,000).
    def test_search_sort_units_picks_largest_in_year(self):
        out = tools.search_recalls(year=2026, sort="units", limit=1)
        self.assertEqual(out["results"][0]["recall_number"], "26102")
        self.assertEqual(out["results"][0]["units"], 15000)
        self.assertEqual(out["sort"], "units")
        self.assertEqual(out["total"], 9)

    # Q3 variation: same sort, different year (2025 max is 25201, 1,200 units).
    def test_search_sort_units_other_year(self):
        out = tools.search_recalls(year=2025, sort="units", limit=1)
        self.assertEqual(out["results"][0]["recall_number"], "25201")
        self.assertEqual(out["results"][0]["units"], 1200)

    # Q3 variation: unknown sort falls back to date (must not break existing search).
    def test_search_unknown_sort_stays_newest_first(self):
        by_date = [r["recall_number"] for r in tools.search_recalls(year=2026)["results"]]
        bogus = [r["recall_number"] for r in tools.search_recalls(year=2026, sort="nope")["results"]]
        self.assertEqual(bogus, by_date)

    # server_status: snapshot health (not a README question).
    def test_status_reports_last_load(self):
        status = tools.server_status()
        self.assertEqual(status["recalls_loaded"], 11)
        self.assertEqual(status["last_load_status"], "ok")
        self.assertEqual(status["last_load_at"], "2026-03-25T02:00:07Z")

    # Response size cap (not a README question).
    def test_fit_keeps_payload_under_budget(self):
        payload = {"total": 400, "results": [{"title": "x" * 900} for _ in range(40)]}
        out = limits.fit(payload)
        import json
        self.assertLessEqual(len(json.dumps(out)), limits.MAX_RESPONSE_CHARS)
        self.assertGreater(len(out["results"]), 0)


if __name__ == "__main__":
    unittest.main()
