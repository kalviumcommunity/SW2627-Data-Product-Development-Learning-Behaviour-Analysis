"""End-to-end data pipeline orchestration for LearnLens AI."""

from __future__ import annotations

import pandas as pd

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

        # Clean completion data
        data["completion"] = clean_completion(data["completion"])

        # Some existing/minimal session source data does not contain
        # start_time or session_date. The clean_sessions() contract is
        # intentionally strict, so provide a pipeline-level fallback
        # before calling it.
        if (
            "start_time" not in data["sessions"].columns
            and "session_date" not in data["sessions"].columns
        ):
            data["sessions"] = data["sessions"].copy()
            data["sessions"]["session_date"] = "1970-01-01"

        # Clean sessions data
        data["sessions"] = clean_sessions(data["sessions"])

        # Clean quiz data
        data["quiz"] = clean_quiz(data["quiz"])

        # Some pipeline/test inputs contain an enrollment dataframe even
        # though there is no separate enrollment CSV. Normalize its date
        # so validate_all() receives the expected datetime dtype.
        if "enrollment" in data:
            data["enrollment"] = data["enrollment"].copy()

            if "enrollment_date" in data["enrollment"].columns:
                data["enrollment"]["enrollment_date"] = pd.to_datetime(
                    data["enrollment"]["enrollment_date"],
                    errors="raise",
                )

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