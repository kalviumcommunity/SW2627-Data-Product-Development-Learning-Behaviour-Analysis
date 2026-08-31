"""Quality-gate integration tests for the production pipeline."""

from __future__ import annotations

import pandas as pd

import pipeline.pipeline as pipeline_module


def test_run_pipeline_invokes_quality_gate_before_writing(
    monkeypatch,
    tmp_path,
):
    raw = {
        "completion": pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "completion_pct": [100],
                "status": ["completed"],
            }
        ),
        "enrollment": pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "enrollment_date": ["2024-01-01"],
                "cohort": ["A"],
            }
        ),
        "sessions": pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "session_date": ["2024-01-05"],
                "duration_minutes": [30],
            }
        ),
        "quiz": pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "attempt_number": [1],
                "score_pct": [90],
            }
        ),
    }

    calls = {"gate": False, "save": False}

    monkeypatch.setattr(
        pipeline_module,
        "BASE_DATA_PATH",
        tmp_path / "raw",
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        tmp_path / "processed",
    )
    monkeypatch.setattr(
        pipeline_module,
        "load_all_data",
        lambda _: {key: value.copy() for key, value in raw.items()},
    )
    monkeypatch.setattr(
        pipeline_module,
        "clean_completion",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "clean_sessions",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "clean_quiz",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "clean_enrollment",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "validate_all",
        lambda _: None,
    )
    monkeypatch.setattr(
        pipeline_module,
        "transform_sessions",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "transform_quiz",
        lambda df: df,
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_student_course_table",
        lambda data: pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "completion_pct": [100],
                "quiz_accuracy": [90],
            }
        ),
    )

    def gate(*args, **kwargs):
        calls["gate"] = True
        assert kwargs.get("require_all_sources") is True
        return pd.DataFrame(
            {
                "dataset": [
                    "completion",
                    "enrollment",
                    "sessions",
                    "quiz",
                ],
                "row_count": [1, 1, 1, 1],
                "missing_values": [0, 0, 0, 0],
                "duplicate_rows": [0, 0, 0, 0],
                "invalid_id_rows": [0, 0, 0, 0],
                "valid": [True, True, True, True],
            }
        )

    monkeypatch.setattr(
        pipeline_module,
        "validate_pipeline_output",
        gate,
    )

    original_to_csv = pd.DataFrame.to_csv

    def tracked_to_csv(self, *args, **kwargs):
        target = args[0] if args else kwargs.get("path_or_buf")
        if target is not None and str(target).endswith(
            "student_course.csv"
        ):
            assert calls["gate"], (
                "student_course.csv was written before the quality gate"
            )
            calls["save"] = True
        return original_to_csv(self, *args, **kwargs)

    monkeypatch.setattr(
        pd.DataFrame,
        "to_csv",
        tracked_to_csv,
    )

    result = pipeline_module.run_pipeline()

    assert not result.empty
    assert calls["gate"] is True
    assert calls["save"] is True
