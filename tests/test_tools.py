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

    def test_search_matches_title(self):
        out = tools.search_recalls("Helmets")
        self.assertEqual([r["recall_number"] for r in out["results"]], ["25202"])

    def test_search_matches_where_sold(self):
        out = tools.search_recalls("Amazon")
        self.assertEqual(out["total"], 3)

    def test_search_matches_hazard(self):
        out = tools.search_recalls("fire")
        self.assertEqual(out["total"], 4)

    def test_search_is_newest_first(self):
        out = tools.search_recalls("")
        dates = [r["recall_date"] for r in out["results"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_year_filter(self):
        self.assertEqual(tools.search_recalls(year=2026)["total"], 8)
        self.assertEqual(tools.search_recalls(year=2025)["total"], 2)

    def test_count_matches_search_total(self):
        for query, year in (("", None), ("fire", None), ("Amazon", 2026), ("", 2025)):
            self.assertEqual(tools.count_recalls(query, year)["count"], tools.search_recalls(query, year)["total"])

    def test_paging_walks_every_row(self):
        seen, cursor = [], 0
        while True:
            out = tools.search_recalls("", limit=3, cursor=cursor)
            seen += [r["recall_number"] for r in out["results"]]
            if "next_cursor" not in out:
                break
            cursor = out["next_cursor"]
        self.assertEqual(len(seen), 10)
        self.assertEqual(len(set(seen)), 10)

    def test_limit_is_clamped(self):
        self.assertEqual(limits.clamp_limit(500), limits.MAX_LIMIT)
        self.assertEqual(limits.clamp_limit(0), limits.DEFAULT_LIMIT)

    def test_get_recall_accepts_dash(self):
        self.assertEqual(tools.get_recall("26-101")["title"], tools.get_recall("26101")["title"])

    def test_get_recall_missing(self):
        self.assertFalse(tools.get_recall("99-999")["found"])

    def test_add_note_shows_on_get_recall(self):
        saved = tools.add_note("26102", "Checked the catalogue, nothing listed.", author="agent:test")
        self.assertTrue(saved["saved"])
        notes = tools.get_recall("26102")["notes"]
        self.assertEqual(notes[-1]["body"], "Checked the catalogue, nothing listed.")
        self.assertEqual(notes[-1]["author"], "agent:test")

    def test_add_note_rejects_empty(self):
        self.assertFalse(tools.add_note("26102", "   ")["saved"])

    def test_recent_recalls_window(self):
        out = tools.recent_recalls(30, today=dt.date(2026, 3, 25))
        self.assertEqual([r["recall_number"] for r in out["results"]], ["26108", "26107", "26106", "26105"])

    def test_status_reports_last_load(self):
        status = tools.server_status()
        self.assertEqual(status["recalls_loaded"], 10)
        self.assertEqual(status["last_load_status"], "ok")
        self.assertEqual(status["last_load_at"], "2026-03-25T02:00:07Z")

    def test_fit_keeps_payload_under_budget(self):
        payload = {"total": 400, "results": [{"title": "x" * 900} for _ in range(40)]}
        out = limits.fit(payload)
        import json
        self.assertLessEqual(len(json.dumps(out)), limits.MAX_RESPONSE_CHARS)
        self.assertGreater(len(out["results"]), 0)


if __name__ == "__main__":
    unittest.main()
