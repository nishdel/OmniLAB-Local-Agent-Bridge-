"""Regression tests: timestamp() must interpret naive values as UTC, not local time."""
import unittest
from datetime import datetime, timezone

from localagentbridge import codex_usage
from localagentbridge.codex_usage import timestamp


class TimestampUtcTests(unittest.TestCase):
    def test_naive_timestamp_is_interpreted_as_utc(self):
        # 2024-01-15T10:30:00 UTC == 1705314600.0
        self.assertEqual(timestamp("2024-01-15T10:30:00"), 1705314600.0)

    def test_z_suffix_is_utc(self):
        self.assertEqual(timestamp("2024-01-15T10:30:00Z"), 1705314600.0)

    def test_explicit_positive_offset(self):
        # 10:30+02:00 == 08:30 UTC == 1705307400.0
        self.assertEqual(timestamp("2024-01-15T10:30:00+02:00"), 1705307400.0)

    def test_explicit_negative_offset(self):
        # 10:30-05:00 == 15:30 UTC == 1705332600.0
        self.assertEqual(timestamp("2024-01-15T10:30:00-05:00"), 1705332600.0)

    def test_naive_and_z_agree(self):
        self.assertEqual(timestamp("2024-06-01T00:00:00"), timestamp("2024-06-01T00:00:00Z"))

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            timestamp("not-a-timestamp")

    def test_non_string_input_raises(self):
        with self.assertRaises((TypeError, AttributeError)):
            timestamp(None)


if __name__ == "__main__":
    unittest.main()

