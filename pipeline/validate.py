import pandas as pd

REQUIRED_SCHEMAS = {
    "completion": ["student_id", "course_id", "completion_pct", "status"],
    "quiz": ["student_id", "course_id", "attempt_number", "score_pct"],
    "sessions": ["student_id", "course_id", "duration_minutes"],
    "enrollment": ["student_id", "course_id", "enrollment_date", "cohort"],
}

NUMERIC_COLUMNS = {
    "completion": ["completion_pct"],
    "quiz": ["attempt_number", "score_pct"],
    "sessions": ["duration_minutes"],
}


def validate_columns(df, required_cols, dataset_name):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} missing columns: {missing}")


def validate_dtypes(df, dataset_name):
    for col in NUMERIC_COLUMNS.get(dataset_name, []):
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"{dataset_name}.{col} must be numeric")


def validate_all(data_dict):
    for name, df in data_dict.items():
        validate_columns(df, REQUIRED_SCHEMAS[name], name)
        validate_dtypes(df, name)