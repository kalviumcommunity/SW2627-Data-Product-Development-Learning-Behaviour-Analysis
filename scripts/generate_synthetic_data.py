"""Reproducible synthetic raw-data generator for development and demos.

The generator is deliberately separate from the production pipeline. It writes
synthetic CSVs only to the explicitly requested output directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DATASET_COLUMNS: dict[str, list[str]] = {
    "completion": [
        "student_id",
        "course_id",
        "completion_pct",
        "status",
    ],
    "enrollment": [
        "student_id",
        "course_id",
        "enrollment_date",
        "cohort",
    ],
    "sessions": [
        "student_id",
        "course_id",
        "session_date",
        "duration_minutes",
    ],
    "quiz": [
        "student_id",
        "course_id",
        "quiz_id",
        "score",
        "attempt",
    ],
}

DEFAULT_SEED = 42
DEFAULT_STUDENTS = 100
DEFAULT_COURSES = 5
DEFAULT_DAYS = 90
DEFAULT_START_DATE = "2024-01-01"


def _validate_args(
    students: int,
    courses: int,
    days: int,
) -> None:
    if students < 1:
        raise ValueError("students must be >= 1")
    if courses < 1:
        raise ValueError("courses must be >= 1")
    if days < 1:
        raise ValueError("days must be >= 1")


def _assignments(
    rng: np.random.Generator,
    students: int,
    courses: int,
) -> list[tuple[str, str]]:
    student_ids = [
        f"S{i:04d}" for i in range(1, students + 1)
    ]
    course_ids = [
        f"C{i:03d}" for i in range(1, courses + 1)
    ]

    result: list[tuple[str, str]] = []

    for student_id in student_ids:
        course_count = int(
            rng.integers(
                1,
                min(courses, 3) + 1,
            )
        )
        selected = rng.choice(
            course_ids,
            size=course_count,
            replace=False,
        )
        result.extend(
            (student_id, str(course_id))
            for course_id in selected
        )

    return result


def generate_datasets(
    *,
    seed: int = DEFAULT_SEED,
    students: int = DEFAULT_STUDENTS,
    courses: int = DEFAULT_COURSES,
    days: int = DEFAULT_DAYS,
    start_date: str = DEFAULT_START_DATE,
) -> dict[str, pd.DataFrame]:
    """Generate internally consistent synthetic raw datasets."""
    _validate_args(
        students,
        courses,
        days,
    )

    rng = np.random.default_rng(seed)

    calendar = pd.date_range(
        start=start_date,
        periods=days,
        freq="D",
    )

    assignments = _assignments(
        rng,
        students,
        courses,
    )

    keys = pd.DataFrame(
        assignments,
        columns=["student_id", "course_id"],
    )

    # Enrollment: exactly one row per student-course.
    enrollment = keys.copy()
    enrollment_offsets = rng.integers(
        0,
        max(1, days // 3),
        size=len(enrollment),
    )
    enrollment["enrollment_date"] = [
        calendar[int(offset)]
        for offset in enrollment_offsets
    ]
    enrollment["cohort"] = rng.choice(
        ["A", "B", "C"],
        size=len(enrollment),
    )

    # Completion: exactly one row per student-course.
    progress = rng.beta(
        a=5,
        b=2,
        size=len(keys),
    ) * 100
    completion = keys.copy()
    completion["completion_pct"] = np.round(
        progress,
        2,
    )
    completion["status"] = pd.cut(
        completion["completion_pct"],
        bins=[
            -np.inf,
            25,
            85,
            np.inf,
        ],
        labels=[
            "dropped",
            "in_progress",
            "completed",
        ],
        right=False,
    ).astype(str)

    # Sessions: one or more event rows per student-course.
    session_rows: list[dict[str, object]] = []
    for student_id, course_id in assignments:
        session_count = int(
            rng.integers(1, 5)
        )
        for _ in range(session_count):
            day_index = int(
                rng.integers(0, days)
            )
            session_rows.append(
                {
                    "student_id": student_id,
                    "course_id": course_id,
                    "session_date": calendar[day_index],
                    "duration_minutes": int(
                        rng.integers(15, 121)
                    ),
                }
            )
    sessions = pd.DataFrame(
        session_rows,
        columns=DATASET_COLUMNS["sessions"],
    )

    # Quizzes: one to three attempts per student-course.
    # Scores correlate loosely with completion to create useful demo patterns.
    quiz_rows: list[dict[str, object]] = []

    for row_index, (student_id, course_id) in enumerate(
        assignments
    ):
        attempts = int(
            rng.integers(1, 4)
        )
        base_score = float(
            completion.iloc[row_index]["completion_pct"]
        )

        for attempt in range(1, attempts + 1):
            score = np.clip(
                base_score + rng.normal(0, 10),
                0,
                100,
            )
            quiz_rows.append(
                {
                    "student_id": student_id,
                    "course_id": course_id,
                    "quiz_id": "Q1",
                    "score": round(float(score), 2),
                    "attempt": attempt,
                }
            )

    quiz = pd.DataFrame(
        quiz_rows,
        columns=DATASET_COLUMNS["quiz"],
    )

    return {
        "completion": completion,
        "enrollment": enrollment,
        "sessions": sessions,
        "quiz": quiz,
    }


def _validate_generated(
    datasets: dict[str, pd.DataFrame],
) -> None:
    """Fail generation if the synthetic data violates its own source contract."""
    if set(datasets) != set(DATASET_COLUMNS):
        raise ValueError("generator produced an unexpected dataset set")

    for name, expected_columns in DATASET_COLUMNS.items():
        frame = datasets[name]

        if list(frame.columns) != expected_columns:
            raise ValueError(
                f"{name} columns do not match the raw-data contract"
            )

        if frame.empty:
            raise ValueError(
                f"{name} must not be empty"
            )

        if frame[
            ["student_id", "course_id"]
        ].isna().any().any():
            raise ValueError(
                f"{name} contains missing identifiers"
            )

    completion = datasets["completion"]
    assert completion["completion_pct"].between(
        0,
        100,
    ).all()

    sessions = datasets["sessions"]
    assert sessions["duration_minutes"].ge(
        0
    ).all()

    quiz = datasets["quiz"]
    assert quiz["score"].between(
        0,
        100,
    ).all()
    assert quiz["attempt"].ge(
        1
    ).all()


def write_datasets(
    output_dir: str | Path,
    *,
    seed: int = DEFAULT_SEED,
    students: int = DEFAULT_STUDENTS,
    courses: int = DEFAULT_COURSES,
    days: int = DEFAULT_DAYS,
    start_date: str = DEFAULT_START_DATE,
    force: bool = False,
) -> dict[str, Path]:
    """Generate and write synthetic CSV files plus a manifest."""
    output = Path(output_dir)
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    datasets = generate_datasets(
        seed=seed,
        students=students,
        courses=courses,
        days=days,
        start_date=start_date,
    )
    _validate_generated(datasets)

    target_paths = {
        name: output / f"{name}.csv"
        for name in datasets
    }
    manifest_path = output / "manifest.json"

    existing = [
        path
        for path in target_paths.values()
        if path.exists()
    ]
    if manifest_path.exists():
        existing.append(manifest_path)

    if existing and not force:
        joined = ", ".join(
            str(path)
            for path in existing
        )
        raise FileExistsError(
            "synthetic-data output already exists: "
            f"{joined}. Use --force to replace it."
        )

    for name, frame in datasets.items():
        frame.to_csv(
            target_paths[name],
            index=False,
        )

    manifest = {
        "generator_version": 1,
        "seed": seed,
        "students": students,
        "courses": courses,
        "days": days,
        "start_date": start_date,
        "datasets": {
            name: {
                "file": target_paths[name].name,
                "rows": int(len(frame)),
                "columns": list(frame.columns),
            }
            for name, frame in datasets.items()
        },
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        **target_paths,
        "manifest": manifest_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate reproducible synthetic LearnLens "
            "raw datasets for development and demos."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )
    parser.add_argument(
        "--students",
        type=int,
        default=DEFAULT_STUDENTS,
    )
    parser.add_argument(
        "--courses",
        type=int,
        default=DEFAULT_COURSES,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing generated files.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    paths = write_datasets(
        args.output_dir,
        seed=args.seed,
        students=args.students,
        courses=args.courses,
        days=args.days,
        start_date=args.start_date,
        force=args.force,
    )

    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
