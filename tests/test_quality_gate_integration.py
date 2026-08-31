"""Integration tests for quality-gate ordering."""

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

    calls = {
        "gate": False,
        "write": False,
    }

    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        tmp_path / "processed",
    )
    monkeypatch.setattr(
        pipeline_module,
        "load_all_data",
        lambda _: {
            key: value.copy()
            for key, value in raw.items()
        },
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

    def tracked_atomic_write(
        frame,
        output_path,
    ):
        assert calls["gate"], (
            "student_course.csv was written before the quality gate"
        )
        calls["write"] = True
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        frame.to_csv(
            output_path,
            index=False,
        )
        return output_path

    monkeypatch.setattr(
        pipeline_module,
        "_atomic_writer_for_test",
        tracked_atomic_write,
        raising=False,
    )

    # Patch the private writer actually used by run_pipeline through the
    # quality_gate module, avoiding brittle DataFrame.to_csv interception.
    import pipeline.quality_gate as quality_gate_module

    monkeypatch.setattr(
        quality_gate_module,
        "_atomic_csv",
        tracked_atomic_write,
    )

    # The test's mocked loader means source mode does not matter.
    result = pipeline_module.run_pipeline()

    assert not result.empty
    assert calls["gate"] is True
    assert calls["write"] is True
