from pipeline.ingest import load_all_data
from pipeline.validate import validate_all
from pipeline.clean import clean_completion, clean_sessions, clean_quiz
from pipeline.transform import transform_sessions, transform_quiz
from pipeline.join import build_student_course_table
from pipeline.logger import logger   


def run_pipeline():
    try:
        logger.info("Loading data...")
        data = load_all_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    try:
        logger.info("Cleaning data...")
        data["completion"] = clean_completion(data["completion"])
        data["sessions"] = clean_sessions(data["sessions"])
        data["quiz"] = clean_quiz(data["quiz"])
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        raise

    try:
        logger.info("Validating data...")
        validate_all(data)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

    logger.info("Transforming data...")
    data["sessions"] = transform_sessions(data["sessions"])
    data["quiz"] = transform_quiz(data["quiz"])

    logger.info("Joining datasets...")
    final_df = build_student_course_table(data)

    logger.info("Saving output...")
    final_df.to_csv("data/processed/student_course.csv", index=False)

    logger.info("Pipeline completed successfully ✅")

    return final_df