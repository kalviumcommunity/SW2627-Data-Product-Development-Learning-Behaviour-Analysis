"""End-to-end LearnLens production data pipeline."""

from __future__ import annotations

from pipeline.clean import (
    clean_completion,
    clean_enrollment,
    clean_quiz,
    clean_sessions,
)
from pipeline.config import PROCESSED_PATH
from pipeline.ingest import load_all_data
from pipeline.join import build_student_course_table
from pipeline.logger import logger
from pipeline.quality_gate import (
    validate_pipeline_output,
    write_pipeline_manifest,
    write_quality_report,
)
from pipeline.transform import (
    transform_quiz,
    transform_sessions,
)
from pipeline.validate import validate_all


def run_pipeline():
    """Generate/load, clean, validate, transform, join, gate, and persist."""
    try:
        logger.info("Loading pipeline source data")
        data = load_all_data()

        logger.info("Cleaning source data")
        data["completion"] = clean_completion(
            data["completion"]
        )
        data["enrollment"] = clean_enrollment(
            data["enrollment"]
        )
        data["sessions"] = clean_sessions(
            data["sessions"]
        )
        data["quiz"] = clean_quiz(
            data["quiz"]
        )

        logger.info("Validating cleaned source data")
        validate_all(data)

        logger.info("Transforming event datasets")
        data["sessions"] = transform_sessions(
            data["sessions"]
        )
        data["quiz"] = transform_quiz(
            data["quiz"]
        )

        logger.info("Building student-course table")
        student_course = build_student_course_table(
            data
        )

        logger.info("Running production quality gate")
        quality_report = validate_pipeline_output(
            {
                "completion": data["completion"],
                "enrollment": data["enrollment"],
                "sessions": data["sessions"],
                "quiz": data["quiz"],
            },
            student_course,
            require_all_sources=True,
        )

        quality_report_path = (
            PROCESSED_PATH
            / "quality_report.csv"
        )
        write_quality_report(
            quality_report,
            quality_report_path,
        )

        output_path = (
            PROCESSED_PATH
            / "student_course.csv"
        )

        from pipeline.quality_gate import _atomic_csv

        _atomic_csv(
            student_course,
            output_path,
        )

        write_pipeline_manifest(
            PROCESSED_PATH
            / "pipeline_manifest.json",
            row_count=len(student_course),
            quality_report_path=quality_report_path,
            student_course_path=output_path,
        )

        logger.info(
            "Pipeline completed successfully: %d rows written",
            len(student_course),
        )
        return student_course

    except Exception:
        logger.exception(
            "Pipeline execution failed"
        )
        raise
