import unittest

import pandas as pd

from pipeline.clean import clean_completion, clean_sessions
from pipeline.ingest import load_csv
from pipeline.validate import validate_all, validate_columns


class PipelineTests(unittest.TestCase):
    def test_missing_columns_raise_error(self) -> None:
        df = pd.DataFrame({"student_id": [1]})

        with self.assertRaises(ValueError):
            validate_columns(df, ["student_id", "course_id"], "completion")

    def test_duplicate_rows_are_removed(self) -> None:
        df = pd.DataFrame(
            {
                "student_id": ["S1", "S1"],
                "course_id": ["C1", "C1"],
                "completion_pct": [75, 75],
                "status": ["Completed", "Completed"],
            }
        )

        cleaned = clean_completion(df)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["status"], "completed")

    def test_null_values_are_handled(self) -> None:
        df = pd.DataFrame(
            {
                "session_id": ["SE1", "SE2"],
                "student_id": ["S1", "S2"],
                "course_id": ["C1", "C1"],
                "start_time": ["2026-01-01", "2026-01-02"],
                "end_time": ["2026-01-01", "2026-01-02"],
                "duration_minutes": [None, 30],
            }
        )

        cleaned = clean_sessions(df)

        self.assertEqual(cleaned.iloc[0]["duration_minutes"], 0)
        self.assertEqual(cleaned.iloc[1]["duration_minutes"], 30)

    def test_load_csv_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_csv("does-not-exist.csv")

    def test_validate_all_passes_on_valid_data(self) -> None:
        data = {
            "completion": pd.DataFrame(
                {
                    "student_id": ["S1"],
                    "course_id": ["C1"],
                    "completion_pct": [90],
                    "status": ["completed"],
                }
            ),
            "quiz": pd.DataFrame(
                {
                    "student_id": ["S1"],
                    "quiz_id": ["Q1"],
                    "course_id": ["C1"],
                    "attempt_number": [1],
                    "score_pct": [80],
                    "timestamp": ["2026-01-01"],
                }
            ),
            "sessions": pd.DataFrame(
                {
                    "session_id": ["SE1"],
                    "student_id": ["S1"],
                    "course_id": ["C1"],
                    "start_time": ["2026-01-01"],
                    "end_time": ["2026-01-01"],
                    "duration_minutes": [30],
                }
            ),
            "enrollment": pd.DataFrame(
                {
                    "student_id": ["S1"],
                    "course_id": ["C1"],
                    "enrollment_date": ["2026-01-01"],
                    "cohort": ["A"],
                }
            ),
        }

        validate_all(data)


if __name__ == "__main__":
    unittest.main()