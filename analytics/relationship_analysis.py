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
OUTPUT_COLUMNS = [
    "feature",
    "target",
    "sample_size",
    "correlation",
    "abs_correlation",
    "strength",
    "direction",
]


def _validate_input(df: pd.DataFrame) -> None:
    missing = sorted(set(BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df[BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]].copy()
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


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
    n = len(pair)

    if n < 2 or pair[feature].nunique() < 2 or pair[TARGET_COLUMN].nunique() < 2:
        return {
            "feature": feature,
            "target": TARGET_COLUMN,
            "sample_size": n,
            "correlation": float("nan"),
            "abs_correlation": float("nan"),
            "strength": "insufficient_data" if n < 2 else "undefined",
            "direction": "unknown",
        }

    value = float(pair[feature].corr(pair[TARGET_COLUMN], method="pearson"))
    return {
        "feature": feature,
        "target": TARGET_COLUMN,
        "sample_size": n,
        "correlation": round(value, 4),
        "abs_correlation": round(abs(value), 4),
        "strength": _strength(value),
        "direction": _direction(value),
    }


def correlate_with_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Measure Pearson association between behavioural features and completion.

    Results describe association only; they are not causal estimates.
    Missing values are handled pairwise for each feature.
    """
    _validate_input(df)
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    frame = _numeric_frame(df)
    result = pd.DataFrame(
        [_relationship(frame, feature) for feature in BEHAVIOURAL_COLUMNS],
        columns=OUTPUT_COLUMNS,
    )
    return result.sort_values(
        ["abs_correlation", "feature"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return Pearson correlations for all behavioural variables and completion."""
    _validate_input(df)
    columns = BEHAVIOURAL_COLUMNS + [TARGET_COLUMN]
    if df.empty:
        return pd.DataFrame(columns=columns, index=columns)
    return _numeric_frame(df)[columns].corr(method="pearson").round(4)


def strongest_relationships(
    df: pd.DataFrame,
    limit: int = 5,
) -> pd.DataFrame:
    """Return up to ``limit`` defined feature/completion relationships."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    result = correlate_with_completion(df)
    return result.loc[result["correlation"].notna()].head(limit).reset_index(drop=True)
