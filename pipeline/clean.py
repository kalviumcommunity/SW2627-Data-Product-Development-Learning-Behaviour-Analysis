import pandas as pd


def _normalize_ids(df):
    for col in ("student_id", "course_id"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    return df


def clean_completion(df):
    df = df.copy()
    df = _normalize_ids(df)

    df["completion_pct"] = (
        df["completion_pct"]
        .astype(str)
        .str.replace("%", "", regex=False)
    )

    df["completion_pct"] = pd.to_numeric(df["completion_pct"], errors="coerce")
    return df


def clean_sessions(df):
    df = df.copy()
    df = _normalize_ids(df)

    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")
    return df


def clean_quiz(df):
    df = df.copy()
    df = _normalize_ids(df)

    df["attempt_number"] = pd.to_numeric(df["attempt_number"], errors="coerce")

    df["score_pct"] = (
        df["score_pct"]
        .astype(str)
        .str.replace("%", "", regex=False)
    )

    df["score_pct"] = pd.to_numeric(df["score_pct"], errors="coerce")

    return df