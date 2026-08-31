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


# =========================
# COMPLETION
# =========================
def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
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


# =========================
# SESSIONS (FIXED PROPERLY)
# =========================
def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    output = _normalize_ids(df)

    required = {"student_id", "course_id", "duration_minutes"}
    missing_required = required - set(output.columns)

    if missing_required:
        raise ValueError(
            "sessions dataset missing required columns: "
            + ", ".join(sorted(missing_required))
        )

    # numeric validation
    output["duration_minutes"] = pd.to_numeric(
        output["duration_minutes"], errors="coerce"
    )

    if output["duration_minutes"].isna().any():
        raise ValueError("sessions.duration_minutes contains non-numeric values")

    if (output["duration_minutes"] < 0).any():
        raise ValueError("sessions.duration_minutes must be greater than or equal to 0")

    # =========================
    # STRICT BEHAVIOR (FOR TEST)
    # =========================
    has_start = "start_time" in output.columns
    has_date = "session_date" in output.columns

    # MUST FAIL for unit test
    if not has_start and not has_date:
        raise ValueError(
            "sessions dataset missing start-time field; expected 'start_time' or 'session_date'"
        )

    # Parse time
    if has_start:
        output["start_time"] = pd.to_datetime(
            output["start_time"], errors="raise"
        )
    else:
        output["start_time"] = pd.to_datetime(
            output["session_date"], errors="raise"
        )

    # ensure clean datetime dtype
    output["start_time"] = output["start_time"].dt.tz_localize(None)

    # compute end time
    output["end_time"] = output["start_time"] + pd.to_timedelta(
        output["duration_minutes"].astype(float),
        unit="m",
    )

    canonical = [
        "student_id",
        "course_id",
        "start_time",
        "end_time",
        "duration_minutes",
    ]

    return output[canonical].reset_index(drop=True)


# =========================
# QUIZ
# =========================
def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
    output = _normalize_ids(df)

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
                "quiz dataset missing attempt column; expected 'attempt_number' or 'attempt'"
            )

    if "score_pct" not in output.columns:
        if "score" in output.columns:
            output = output.rename(columns={"score": "score_pct"})
        else:
            raise ValueError(
                "quiz dataset missing score column; expected 'score_pct' or 'score'"
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


# =========================
# ENROLLMENT (FIXED DTYPE ISSUE)
# =========================
def clean_enrollment(df: pd.DataFrame) -> pd.DataFrame:
    output = _normalize_ids(df)

    required = {"student_id", "course_id"}
    missing_required = required - set(output.columns)

    if missing_required:
        raise ValueError(
            "enrollment dataset missing required columns: "
            + ", ".join(sorted(missing_required))
        )

    if "enrollment_date" in output.columns:
        output["enrollment_date"] = pd.to_datetime(
            output["enrollment_date"],
            errors="raise"
        )

        output["enrollment_date"] = output["enrollment_date"].dt.tz_localize(None)

    else:
        # IMPORTANT: keep correct dtype for validator
        output["enrollment_date"] = pd.Series(
            [pd.NaT] * len(output),
            dtype="datetime64[ns]"
        )

    return output.reset_index(drop=True)