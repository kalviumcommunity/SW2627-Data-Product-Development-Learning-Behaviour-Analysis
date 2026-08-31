"""Canonical source-data cleaning and normalization."""

from __future__ import annotations

import pandas as pd


def _normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for col in ("student_id", "course_id"):
        if col in output.columns:
            output[col] = output[col].astype("string").str.strip()
    return output


def _require_columns(
    df: pd.DataFrame,
    required: set[str],
    dataset_name: str,
) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            f"{dataset_name} dataset missing columns: {', '.join(missing)}"
        )


def _strict_numeric(
    series: pd.Series,
    field_name: str,
    *,
    allow_missing: bool = False,
) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & converted.isna()
    if invalid.any():
        raise ValueError(f"{field_name} contains non-numeric values")
    if not allow_missing and converted.isna().any():
        raise ValueError(f"{field_name} contains missing values")
    if not pd.Series(converted).map(pd.notna).all():
        return converted
    return converted


def _strict_datetime(
    series: pd.Series,
    field_name: str,
) -> pd.Series:
    parsed = pd.to_datetime(
    series,
    format="%Y-%m-%d",
    errors="coerce",
)
    invalid = series.notna() & parsed.isna()

    if invalid.any():
        raise ValueError(
            f"{field_name} contains invalid datetime values"
        )
    if parsed.isna().any():
        raise ValueError(
            f"{field_name} contains missing datetime values"
        )

    if getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_convert("UTC").dt.tz_localize(None)

    return parsed


def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize completion data and reject malformed numeric values."""
    output = _normalize_ids(df.drop_duplicates())

    _require_columns(
        output,
        {"student_id", "course_id", "status", "completion_pct"},
        "completion",
    )

    output["status"] = (
        output["status"]
        .astype("string")
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    raw = (
        output["completion_pct"]
        .astype("string")
        .str.strip()
        .str.replace("%", "", regex=False)
    )
    output["completion_pct"] = _strict_numeric(
        raw,
        "completion.completion_pct",
    )

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError(
            "completion.completion_pct must be within the range 0-100"
        )

    if output[["student_id", "course_id"]].isna().any().any():
        raise ValueError(
            "completion identifiers cannot be missing"
        )

    return output.reset_index(drop=True)


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize sessions while preserving source columns.

    The raw source contract may provide either ``start_time`` or
    ``session_date``. One real source timestamp is required; no timestamp is
    fabricated.
    """
    output = _normalize_ids(df)

    _require_columns(
        output,
        {"student_id", "course_id", "duration_minutes"},
        "sessions",
    )

    duration = _strict_numeric(
        output["duration_minutes"],
        "sessions.duration_minutes",
    )
    if not duration.between(0, float("inf")).all():
        raise ValueError(
            "sessions.duration_minutes must be finite and non-negative"
        )
    output["duration_minutes"] = duration

    if "start_time" in output.columns:
        output["start_time"] = _strict_datetime(
            output["start_time"],
            "sessions.start_time",
        )
    elif "session_date" in output.columns:
        output["start_time"] = _strict_datetime(
            output["session_date"],
            "sessions.session_date",
        )
    else:
        raise ValueError(
            "sessions dataset missing start-time field; expected "
            "'start_time' or 'session_date'"
        )

    output["end_time"] = (
        output["start_time"]
        + pd.to_timedelta(output["duration_minutes"], unit="m")
    )

    return output.reset_index(drop=True)


def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize quiz schema to canonical analytics column names."""
    output = _normalize_ids(df)

    _require_columns(
        output,
        {"student_id", "course_id"},
        "quiz",
    )

    if "attempt_number" not in output.columns:
        if "attempt" in output.columns:
            output = output.rename(columns={"attempt": "attempt_number"})
        else:
            raise ValueError(
                "quiz dataset missing attempt column; expected "
                "'attempt_number' or 'attempt'"
            )

    if "score_pct" not in output.columns:
        if "score" in output.columns:
            output = output.rename(columns={"score": "score_pct"})
        else:
            raise ValueError(
                "quiz dataset missing score column; expected "
                "'score_pct' or 'score'"
            )

    output["attempt_number"] = _strict_numeric(
        output["attempt_number"],
        "quiz.attempt_number",
    )
    if not output["attempt_number"].between(1, float("inf")).all():
        raise ValueError(
            "quiz.attempt_number must be finite and greater than or equal to 1"
        )

    raw_score = (
        output["score_pct"]
        .astype("string")
        .str.strip()
        .str.replace("%", "", regex=False)
    )
    output["score_pct"] = _strict_numeric(
        raw_score,
        "quiz.score_pct",
    )
    if not output["score_pct"].between(0, 100).all():
        raise ValueError(
            "quiz.score_pct must be within the range 0-100"
        )

    # Timestamp is optional because the actual raw quiz dataset currently
    # contains no timestamp. When present, validate rather than fabricate.
    if "timestamp" in output.columns:
        output["timestamp"] = _strict_datetime(
            output["timestamp"],
            "quiz.timestamp",
        )

    return output.reset_index(drop=True)


def clean_enrollment(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize enrollment data and validate its temporal field."""
    output = _normalize_ids(df)

    _require_columns(
        output,
        {"student_id", "course_id", "enrollment_date", "cohort"},
        "enrollment",
    )

    output["enrollment_date"] = _strict_datetime(
        output["enrollment_date"],
        "enrollment.enrollment_date",
    )
    output["cohort"] = (
        output["cohort"].astype("string").str.strip()
    )

    return output.reset_index(drop=True)
