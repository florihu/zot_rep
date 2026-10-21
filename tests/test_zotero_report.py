import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import zotero_report as zr


class DefaultDbPathTest(unittest.TestCase):
    def test_env_var_takes_precedence(self):
        with mock.patch.dict(os.environ, {"ZOTERO_DB": "~/custom/zotero.sqlite"}):
            self.assertEqual(zr.default_db_path(), Path.home() / "custom" / "zotero.sqlite")

    def test_falls_back_to_auto_discovery_without_env_var(self):
        env = {k: v for k, v in os.environ.items() if k != "ZOTERO_DB"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertIn(
                zr.default_db_path(),
                [Path.home() / "Zotero" / "zotero.sqlite",
                 Path.home() / ".zotero" / "zotero" / "zotero.sqlite"],
            )


class DefaultOutDirTest(unittest.TestCase):
    def test_rep_next_to_script_with_collection_name_only(self):
        out = zr.default_out_dir("Copper PSUT")
        self.assertEqual(out, Path(zr.__file__).resolve().parent / "rep" / "Copper_PSUT")

    def test_collection_name_is_sanitised(self):
        out = zr.default_out_dir("  a/b: c!  ")
        self.assertEqual(out.name, "a_b_c")


def ann(type_, text="", comment=""):
    return {"type": type_, "highlighted_text": text, "comment": comment, "color": None, "page": None}


class AnnotationStatsTest(unittest.TestCase):
    def test_counts_by_type_and_comment(self):
        stats = zr.annotation_stats([
            ann("highlight", "one two three"),
            ann("highlight", "one", "my note here"),
            ann("underline", "a b"),
            ann("note", comment="sticky"),
            ann("image"),
        ])
        self.assertEqual(stats["annotations"], 5)
        self.assertEqual(stats["highlights"], 2)
        self.assertEqual(stats["underlines"], 1)
        self.assertEqual(stats["comments"], 2)

    def test_text_average_pools_highlights_and_underlines(self):
        stats = zr.annotation_stats([
            ann("highlight", "one two three"),
            ann("underline", "a b"),
            ann("highlight", "x"),
        ])
        self.assertEqual(stats["avg_text_words"], 2.0)

    def test_averages_are_rounded_to_one_decimal(self):
        stats = zr.annotation_stats([
            ann("highlight", "a", "a b"),
            ann("highlight", "a b", "a"),
            ann("highlight", "a b", "a"),
        ])
        self.assertEqual(stats["avg_text_words"], 1.7)
        self.assertEqual(stats["avg_comment_words"], 1.3)

    def test_empty_averages_are_none(self):
        stats = zr.annotation_stats([])
        self.assertEqual(stats["annotations"], 0)
        self.assertIsNone(stats["avg_text_words"])
        self.assertIsNone(stats["avg_comment_words"])


class StatsSummaryTest(unittest.TestCase):
    def test_full_summary(self):
        stats = {"annotations": 12, "highlights": 7, "underlines": 4, "comments": 2,
                 "avg_text_words": 23.4, "avg_comment_words": 8.0}
        self.assertEqual(
            zr.stats_summary(stats),
            "12 annotations (7 highlights, 4 underlines, 2 comments)"
            " · ⌀ 23.4 words/highlight · ⌀ 8.0 words/comment",
        )

    def test_missing_averages_are_omitted(self):
        stats = {"annotations": 1, "highlights": 1, "underlines": 0, "comments": 0,
                 "avg_text_words": 5.0, "avg_comment_words": None}
        self.assertEqual(
            zr.stats_summary(stats),
            "1 annotations (1 highlights, 0 underlines, 0 comments) · ⌀ 5.0 words/highlight",
        )


class MarkdownStatsTest(unittest.TestCase):
    def record(self, annotations):
        return {"title": "T", "authors": [], "year": "", "publication": "", "doi": "",
                "tags": [], "abstract": "", "annotations": annotations, "notes": [],
                "stats": zr.annotation_stats(annotations)}

    def test_item_with_annotations_gets_stats_line(self):
        md = zr.to_markdown("C", [self.record([ann("highlight", "a b")])])
        self.assertIn("**Annotations:** 1 annotations", md)

    def test_item_without_annotations_has_no_stats_line(self):
        md = zr.to_markdown("C", [self.record([])])
        self.assertNotIn("**Annotations:**", md)

    def test_header_has_collection_summary(self):
        md = zr.to_markdown("C", [self.record([ann("highlight", "a b")]), self.record([])])
        self.assertIn("*2 item(s) · 1 annotations (1 highlights", md)


if __name__ == "__main__":
    unittest.main()
