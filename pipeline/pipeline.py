from pipeline.ingest import load_all_data
from pipeline.validate import validate_all
from pipeline.clean import clean_completion, clean_sessions, clean_quiz
from pipeline.transform import transform_sessions, transform_quiz
from pipeline.join import build_student_course_table


def run_pipeline():
    data = load_all_data()

    # CLEAN
    data["completion"] = clean_completion(data["completion"])
    data["sessions"] = clean_sessions(data["sessions"])
    data["quiz"] = clean_quiz(data["quiz"])

    # VALIDATE
    validate_all(data)

    # TRANSFORM
    data["sessions"] = transform_sessions(data["sessions"])
    data["quiz"] = transform_quiz(data["quiz"])

    # JOIN
    final_df = build_student_course_table(data)

    # SAVE
    final_df.to_csv("data/processed/student_course.csv", index=False)

    return final_df