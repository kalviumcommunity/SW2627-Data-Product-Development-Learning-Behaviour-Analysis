"""Behavioural relationship analysis for LearnLens AI."""
from __future__ import annotations

import pandas as pd

BEHAVIOURAL_COLUMNS = [
    "total_study_hours",
    "avg_session_length",
    "quiz_accuracy",
    "quiz_frequency",
    "active_days",
    "learning_streak",
    "days_since_last_activity",
    "weekly_sessions",
]
TARGET_COLUMN = "completion_pct"
MIN_CORRELATION_SAMPLES = 3

OUTPUT_COLUMNS = [
    "feature",
    "target",
    "sample_size",
    "correlation",
    "abs_correlation",
    "strength",
    "direction",
]

NON_NEGATIVE_COLUMNS = [
    "total_study_hours",
    "avg_session_length",
    "quiz_frequency",
    "active_days",
    "learning_streak",
    "days_since_last_activity",
    "weekly_sessions",
]


def _validate_input(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    missing = sorted(
        set(BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]) - set(df.columns)
    )
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Convert valid numeric values and reject malformed non-null values."""
    frame = df[BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]].copy()

    for column in frame.columns:
        original = frame[column]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & converted.isna()

        if invalid.any():
            raise ValueError(
                f"{column} contains non-numeric values"
            )

        frame[column] = converted

    return frame


def _validate_ranges(frame: pd.DataFrame) -> None:
    completion = frame[TARGET_COLUMN].dropna()
    if not completion.between(0, 100).all():
        raise ValueError(
            "completion_pct must be within the range 0-100"
        )

    quiz = frame["quiz_accuracy"].dropna()
    if not quiz.between(0, 100).all():
        raise ValueError(
            "quiz_accuracy must be within the range 0-100"
        )

    for column in NON_NEGATIVE_COLUMNS:
        values = frame[column].dropna()
        if (values < 0).any():
            raise ValueError(
                f"{column} must be greater than or equal to 0"
            )


def _strength(value: float) -> str:
    value = abs(value)
    if value >= 0.70:
        return "strong"
    if value >= 0.40:
        return "moderate"
    if value >= 0.20:
        return "weak"
    return "very_weak"


def _direction(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "none"


def _relationship(frame: pd.DataFrame, feature: str) -> dict[str, object]:
    pair = frame[[feature, TARGET_COLUMN]].dropna()
    sample_size = len(pair)

    if sample_size < MIN_CORRELATION_SAMPLES:
        return {
            "feature": feature,
            "target": TARGET_COLUMN,
            "sample_size": sample_size,
            "correlation": float("nan"),
            "abs_correlation": float("nan"),
            "strength": "insufficient_data",
            "direction": "unknown",
        }

    if pair[feature].nunique() < 2 or pair[TARGET_COLUMN].nunique() < 2:
        return {
            "feature": feature,
            "target": TARGET_COLUMN,
            "sample_size": sample_size,
            "correlation": float("nan"),
            "abs_correlation": float("nan"),
            "strength": "undefined",
            "direction": "unknown",
        }

    value = float(
        pair[feature].corr(pair[TARGET_COLUMN], method="pearson")
    )

    return {
        "feature": feature,
        "target": TARGET_COLUMN,
        "sample_size": sample_size,
        "correlation": round(value, 4),
        "abs_correlation": round(abs(value), 4),
        "strength": _strength(value),
        "direction": _direction(value),
    }


def correlate_with_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Measure Pearson association with completion.

    Missing values are handled pairwise. Malformed non-null values raise.
    """
    _validate_input(df)

    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    frame = _numeric_frame(df)
    _validate_ranges(frame)

    result = pd.DataFrame(
        [_relationship(frame, feature) for feature in BEHAVIOURAL_COLUMNS],
        columns=OUTPUT_COLUMNS,
    )

    return (
        result.sort_values(
            ["abs_correlation", "feature"],
            ascending=[False, True],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return the Pearson correlation matrix for behavioural variables."""
    _validate_input(df)
    columns = BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]

    if df.empty:
        return pd.DataFrame(columns=columns, index=columns)

    frame = _numeric_frame(df)
    _validate_ranges(frame)

    matrix = frame[columns].corr(method="pearson")

    for feature in BEHAVIOURAL_COLUMNS:
        pair = frame[[feature, TARGET_COLUMN]].dropna()
        if (
            len(pair) < MIN_CORRELATION_SAMPLES
            or pair[feature].nunique() < 2
            or pair[TARGET_COLUMN].nunique() < 2
        ):
            matrix.loc[feature, TARGET_COLUMN] = float("nan")
            matrix.loc[TARGET_COLUMN, feature] = float("nan")

    return matrix.round(4)


def strongest_relationships(
    df: pd.DataFrame,
    limit: int = 5,
) -> pd.DataFrame:
    """Return up to ``limit`` defined feature/completion relationships."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    return (
        correlate_with_completion(df)
        .loc[lambda result: result["correlation"].notna()]
        .head(limit)
        .reset_index(drop=True)
    )
