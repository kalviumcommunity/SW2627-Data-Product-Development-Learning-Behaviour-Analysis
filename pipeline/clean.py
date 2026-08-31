"""Canonical cleaning functions for LearnLens pipeline datasets."""

from __future__ import annotations

import pandas as pd


def _normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()

    for column in ("student_id", "course_id"):
        if column in output.columns:
            output[column] = (
                output[column]
                .astype("string")
                .str.strip()
            )

    return output


def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and type-clean completion records."""
    output = _normalize_ids(df.drop_duplicates())

    required = {
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    }
    missing = sorted(required - set(output.columns))

    if missing:
        raise ValueError(
            f"completion dataset missing columns: {', '.join(missing)}"
        )

    output["status"] = (
        output["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    output["completion_pct"] = pd.to_numeric(
        output["completion_pct"]
        .astype("string")
        .str.replace("%", "", regex=False),
        errors="coerce",
    )

    return output


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw session schema to canonical time fields.

    The current raw dataset provides ``session_date`` and
    ``duration_minutes``. ``session_date`` is normalized to ``start_time``.
    When an exact time-of-day is unavailable, the timestamp is anchored at
    midnight rather than inventing precision.

    ``end_time`` is derived from the canonical start time and duration.
    """
    output = _normalize_ids(df)

    required = {
        "student_id",
        "course_id",
        "duration_minutes",
    }

    if "start_time" not in output.columns and "session_date" not in output.columns:
        raise ValueError(
            "sessions dataset missing start-time field; expected "
            "'start_time' or 'session_date'"
        )

    missing = sorted(required - set(output.columns))
    if missing:
        raise ValueError(
            f"sessions dataset missing columns: {', '.join(missing)}"
        )

    if "start_time" not in output.columns:
        output["start_time"] = pd.to_datetime(
            output["session_date"],
            errors="coerce",
        ).dt.normalize()
    else:
        output["start_time"] = pd.to_datetime(
            output["start_time"],
            errors="coerce",
        )

    output["duration_minutes"] = pd.to_numeric(
        output["duration_minutes"],
        errors="coerce",
    )

    invalid_duration = (
        output["duration_minutes"].notna()
        & (output["duration_minutes"] < 0)
    )

    if invalid_duration.any():
        raise ValueError(
            "sessions.duration_minutes must be greater than or equal to 0"
        )

    output["end_time"] = (
        output["start_time"]
        + pd.to_timedelta(
            output["duration_minutes"],
            unit="m",
        )
    )

    return output


def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize quiz score/attempt fields and optional timestamps.

    The current raw dataset uses ``attempt`` and ``score``. These are mapped
    to canonical ``attempt_number`` and ``score_pct``. A quiz timestamp is
    standardized when supplied, but is not fabricated when absent.
    """
    output = _normalize_ids(df)

    required_ids = {"student_id", "course_id"}
    missing_ids = sorted(required_ids - set(output.columns))

    if missing_ids:
        raise ValueError(
            f"quiz dataset missing columns: {', '.join(missing_ids)}"
        )

    if "attempt_number" not in output.columns:
        if "attempt" in output.columns:
            output = output.rename(
                columns={"attempt": "attempt_number"}
            )
        else:
            raise ValueError(
                "quiz dataset missing attempt column; expected "
                "'attempt_number' or 'attempt'"
            )

    if "score_pct" not in output.columns:
        if "score" in output.columns:
            output = output.rename(
                columns={"score": "score_pct"}
            )
        else:
            raise ValueError(
                "quiz dataset missing score column; expected "
                "'score_pct' or 'score'"
            )

    output["attempt_number"] = pd.to_numeric(
        output["attempt_number"],
        errors="coerce",
    )

    output["score_pct"] = pd.to_numeric(
        output["score_pct"]
        .astype("string")
        .str.replace("%", "", regex=False),
        errors="coerce",
    )

    if "timestamp" in output.columns:
        output["timestamp"] = pd.to_datetime(
            output["timestamp"],
            errors="coerce",
        )

    return output
