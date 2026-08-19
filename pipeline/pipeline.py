import logging

from pipeline.config import BASE_DATA_PATH, PROCESSED_PATH

logger = logging.getLogger(__name__)


def run_pipeline():
    try:
        data = load_all_data(BASE_DATA_PATH)
    except Exception:
        logger.exception("Data loading failed")
        raise

    try:
        cleaned_data = clean_data(data)
    except Exception:
        logger.exception("Data cleaning failed")
        raise

    try:
        validated_data = validate_data(cleaned_data)
    except Exception:
        logger.exception("Data validation failed")
        raise

    try:
        transformed_data = transform_data(validated_data)
    except Exception:
        logger.exception("Data transformation failed")
        raise

    try:
        student_course = join_data(transformed_data)
    except Exception:
        logger.exception("Data joining failed")
        raise

    output_path = PROCESSED_PATH / "student_course.csv"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        student_course.to_csv(output_path, index=False)
    except Exception:
        logger.exception("Saving processed data failed")
        raise

    return student_course
