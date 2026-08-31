"""Join pipeline datasets with explicit grain contracts."""

from __future__ import annotations

import pandas as pd


KEYS = ["student_id", "course_id"]


def _require_unique(df: pd.DataFrame, name: str) -> None:
    duplicates = int(
        df.duplicated(subset=KEYS, keep=False).sum()
    )
    if duplicates:
        raise ValueError(
            f"{name} contains {duplicates} rows with duplicate "
            "student-course keys"
        )


def build_student_course_table(
    data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build one row per student-course using aggregated event tables."""
    enrollment = data["enrollment"].copy()
    completion = data["completion"].copy()
    sessions = data["sessions"].copy()
    quiz = data["quiz"].copy()

    for name, df in (
        ("enrollment", enrollment),
        ("completion", completion),
        ("sessions", sessions),
        ("quiz", quiz),
    ):
        for key in KEYS:
            if key not in df.columns:
                raise ValueError(
                    f"{name} missing join key: {key}"
                )

    _require_unique(enrollment, "enrollment")
    _require_unique(completion, "completion")
    _require_unique(sessions, "sessions")
    _require_unique(quiz, "quiz")

    result = enrollment.merge(
        completion,
        on=KEYS,
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        sessions,
        on=KEYS,
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        quiz,
        on=KEYS,
        how="left",
        validate="one_to_one",
    )

    if result.duplicated(subset=KEYS, keep=False).any():
        raise ValueError(
            "student-course join produced duplicate keys"
        )

    return result.reset_index(drop=True)
