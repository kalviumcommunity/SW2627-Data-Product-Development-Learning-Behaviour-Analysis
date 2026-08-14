def build_student_course_table(data):
    enrollment = data["enrollment"]
    completion = data["completion"]
    sessions = data["sessions"]
    quiz = data["quiz"]

    df = enrollment.copy()

    df = df.merge(completion, on=["student_id", "course_id"], how="left")
    df = df.merge(sessions, on=["student_id", "course_id"], how="left")
    df = df.merge(quiz, on=["student_id", "course_id"], how="left")

    return df