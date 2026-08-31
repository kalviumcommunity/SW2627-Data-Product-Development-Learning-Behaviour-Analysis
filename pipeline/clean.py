"""Canonical cleaning functions for LearnLens pipeline datasets."""

from __future__ import annotations

import pandas as pd


def _normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for column in ("student_id", "course_id"):
        if column in output.columns:
            output[column] = output[column].astype("string").str.strip()
    return output


def _parse_datetime_strict(series: pd.Series, field_name: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    invalid = series.notna() & parsed.isna()
    if invalid.any():
        raise ValueError(f"{field_name} contains invalid datetime values")
    if parsed.isna().any():
        raise ValueError(f"{field_name} contains missing datetime values")
    # Normalize timezone-aware values to naive UTC before downstream use.
    if getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
    return parsed


def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
    output = _normalize_ids(df.drop_duplicates())
    required = {"student_id", "course_id", "status", "completion_pct"}
    missing = sorted(required - set(output.columns))
    if missing:
        raise ValueError(
            f"completion dataset missing columns: {', '.join(missing)}"
        )

    output["status"] = (
        output["status"].astype("string").str.strip().str.lower()
    )
    raw = output["completion_pct"].astype("string").str.replace(
        "%", "", regex=False
    )
    numeric = pd.to_numeric(raw, errors="coerce")
    invalid = raw.notna() & numeric.isna()
    if invalid.any():
        raise ValueError("completion.completion_pct contains non-numeric values")
    output["completion_pct"] = numeric
    return output


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize source session dates without fabricating timestamps."""
    output = _normalize_ids(df.copy())

    required = {"student_id", "course_id", "duration_minutes"}
    missing = sorted(required - set(output.columns))
    if missing:
        raise ValueError(
            "sessions dataset missing required columns: " + ", ".join(missing)
        )

    duration_raw = output["duration_minutes"]
    duration = pd.to_numeric(duration_raw, errors="coerce")
    invalid_duration = duration_raw.notna() & duration.isna()
    if invalid_duration.any():
        raise ValueError(
            "sessions.duration_minutes contains non-numeric values"
        )
    if duration.isna().any():
        raise ValueError("sessions.duration_minutes contains missing values")
    if (duration < 0).any():
        raise ValueError(
            "sessions.duration_minutes must be greater than or equal to 0"
        )
    output["duration_minutes"] = duration

    if "start_time" in output.columns:
        parsed = _parse_datetime_strict(
            output["start_time"], "sessions.start_time"
        )
    elif "session_date" in output.columns:
        parsed = _parse_datetime_strict(
            output["session_date"], "sessions.session_date"
        )
    else:
        raise ValueError(
            "sessions dataset missing start-time field; expected "
            "'start_time' or 'session_date'"
        )

    output["start_time"] = parsed
    output["end_time"] = (
        output["start_time"]
        + pd.to_timedelta(output["duration_minutes"], unit="m")
    )

    # Preserve all source columns while exposing canonical timestamps.
    return output.reset_index(drop=True)


def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize quiz schema without inventing timestamps."""
    output = _normalize_ids(df.copy())

    required_ids = {"student_id", "course_id"}
    missing_ids = sorted(required_ids - set(output.columns))
    if missing_ids:
        raise ValueError(
            f"quiz dataset missing columns: {', '.join(missing_ids)}"
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

    attempts_raw = output["attempt_number"]
    attempts = pd.to_numeric(attempts_raw, errors="coerce")
    invalid_attempts = attempts_raw.notna() & attempts.isna()
    if invalid_attempts.any():
        raise ValueError("quiz.attempt_number contains non-numeric values")
    if attempts.isna().any():
        raise ValueError("quiz.attempt_number contains missing values")
    if (attempts < 1).any():
        raise ValueError(
            "quiz.attempt_number must be greater than or equal to 1"
        )
    output["attempt_number"] = attempts

    raw_score = output["score_pct"].astype("string").str.replace(
        "%", "", regex=False
    )
    scores = pd.to_numeric(raw_score, errors="coerce")
    invalid_scores = raw_score.notna() & scores.isna()
    if invalid_scores.any():
        raise ValueError("quiz.score_pct contains non-numeric values")
    if scores.isna().any():
        raise ValueError("quiz.score_pct contains missing values")
    if not scores.between(0, 100).all():
        raise ValueError("quiz.score_pct must be within the range 0-100")
    output["score_pct"] = scores

    if "timestamp" in output.columns:
        output["timestamp"] = _parse_datetime_strict(
            output["timestamp"], "quiz.timestamp"
        )

    return output.reset_index(drop=True)


def clean_enrollment(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize enrollment data and validate its source date."""
    output = _normalize_ids(df.copy())
    required = {"student_id", "course_id", "enrollment_date", "cohort"}
    missing = sorted(required - set(output.columns))
    if missing:
        raise ValueError(
            "enrollment dataset missing required columns: "
            + ", ".join(missing)
        )

    output["enrollment_date"] = _parse_datetime_strict(
        output["enrollment_date"], "enrollment.enrollment_date"
    )
    output["cohort"] = output["cohort"].astype("string").str.strip()
    return output.reset_index(drop=True)
