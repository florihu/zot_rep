import datetime
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
    def test_colrep_next_to_script_with_collection_and_date(self):
        out = zr.default_out_dir("Copper PSUT", datetime.date(2026, 10, 6))
        self.assertEqual(out, Path(zr.__file__).resolve().parent / "colrep" / "Copper_PSUT_2026-10-06")

    def test_collection_name_is_sanitised(self):
        out = zr.default_out_dir("  a/b: c!  ", datetime.date(2026, 1, 2))
        self.assertEqual(out.name, "a_b_c_2026-01-02")


if __name__ == "__main__":
    unittest.main()
