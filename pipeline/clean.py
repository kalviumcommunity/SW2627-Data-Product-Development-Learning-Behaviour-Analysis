"""Canonical cleaning functions for LearnLens pipeline datasets."""

from __future__ import annotations

import pandas as pd


def _normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("student_id", "course_id"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    return df


def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    df = _normalize_ids(df)

    required = {"student_id", "course_id", "status", "completion_pct"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            f"completion dataset missing columns: {', '.join(missing)}"
        )

    df["status"] = (
        df["status"]
        .fillna("")
        .astype("string")
        .str.lower()
        .str.strip()
    )

    df["completion_pct"] = (
        df["completion_pct"]
        .astype("string")
        .str.replace("%", "", regex=False)
    )
    df["completion_pct"] = pd.to_numeric(
        df["completion_pct"],
        errors="coerce",
    )

    return df


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = _normalize_ids(df)

    required = {
        "student_id",
        "course_id",
        "duration_minutes",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            f"sessions dataset missing columns: {', '.join(missing)}"
        )

    df["duration_minutes"] = pd.to_numeric(
        df["duration_minutes"],
        errors="coerce",
    )

    return df


def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize quiz schema to the canonical internal contract.

    The current raw dataset uses ``attempt`` and ``score`` while older
    pipeline code expects ``attempt_number`` and ``score_pct``. Accept both
    forms and normalize to the canonical names so existing analytics and
    dashboard features continue to work.
    """
    df = df.copy()
    df = _normalize_ids(df)

    required_ids = {"student_id", "course_id"}
    missing_ids = sorted(required_ids - set(df.columns))
    if missing_ids:
        raise ValueError(
            f"quiz dataset missing columns: {', '.join(missing_ids)}"
        )

    # Backward/forward-compatible schema normalization.
    if "attempt_number" not in df.columns:
        if "attempt" in df.columns:
            df = df.rename(columns={"attempt": "attempt_number"})
        else:
            raise ValueError(
                "quiz dataset missing attempt column; expected "
                "'attempt_number' or 'attempt'"
            )

    if "score_pct" not in df.columns:
        if "score" in df.columns:
            df = df.rename(columns={"score": "score_pct"})
        else:
            raise ValueError(
                "quiz dataset missing score column; expected "
                "'score_pct' or 'score'"
            )

    df["attempt_number"] = pd.to_numeric(
        df["attempt_number"],
        errors="coerce",
    )

    df["score_pct"] = (
        df["score_pct"]
        .astype("string")
        .str.replace("%", "", regex=False)
    )
    df["score_pct"] = pd.to_numeric(
        df["score_pct"],
        errors="coerce",
    )

    return df
