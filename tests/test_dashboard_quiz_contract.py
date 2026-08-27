"""Frontend data-contract regression tests.

These tests ensure the same cleaned quiz data consumed by Streamlit exposes
the canonical fields required by Overview and Student Behaviour analytics.
"""

import pandas as pd

from pipeline.clean import clean_quiz


def test_dashboard_quiz_contract():
    raw = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "quiz_id": ["Q1"],
            "score": [90],
            "attempt": [1],
        }
    )

    cleaned = clean_quiz(raw)

    assert {"student_id", "course_id", "score_pct", "attempt_number"} <= set(
        cleaned.columns
    )
    assert cleaned.loc[0, "score_pct"] == 90
    assert cleaned.loc[0, "attempt_number"] == 1
