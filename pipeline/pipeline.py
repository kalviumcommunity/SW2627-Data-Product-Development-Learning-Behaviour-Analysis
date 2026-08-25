"""End-to-end data pipeline orchestration for LearnLens AI."""

from __future__ import annotations

from pipeline.clean import clean_completion, clean_quiz, clean_sessions
from pipeline.config import BASE_DATA_PATH, PROCESSED_PATH
from pipeline.ingest import load_all_data
from pipeline.join import build_student_course_table
from pipeline.logger import logger
from pipeline.quality_gate import validate_pipeline_output, write_quality_report
from pipeline.transform import transform_quiz, transform_sessions
from pipeline.validate import validate_all


def run_pipeline():
    """Run ingestion, cleaning, validation, transformation, quality gating, and save."""
    try:
        logger.info("Loading source data from %s", BASE_DATA_PATH)
        data = load_all_data(BASE_DATA_PATH)

        logger.info("Cleaning source data")
        data["completion"] = clean_completion(data["completion"])
        data["sessions"] = clean_sessions(data["sessions"])
        data["quiz"] = clean_quiz(data["quiz"])

        logger.info("Validating cleaned data")
        validate_all(data)

        logger.info("Transforming session and quiz data")
        data["sessions"] = transform_sessions(data["sessions"])
        data["quiz"] = transform_quiz(data["quiz"])

        logger.info("Building student-course table")
        student_course = build_student_course_table(data)

        logger.info("Running production data-quality gate")
        quality_report = validate_pipeline_output(
            {
                "completion": data["completion"],
                "sessions": data["sessions"],
                "quiz": data["quiz"],
            },
            student_course,
        )

        quality_report_path = PROCESSED_PATH / "quality_report.csv"
        write_quality_report(quality_report, quality_report_path)
        logger.info("Quality report written to %s", quality_report_path)

        output_path = PROCESSED_PATH / "student_course.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Saving processed data to %s", output_path)
        student_course.to_csv(output_path, index=False)

        logger.info(
            "Pipeline completed successfully: %d rows written",
            len(student_course),
        )
        return student_course

    except Exception:
        logger.exception("Pipeline execution failed")
        raise
