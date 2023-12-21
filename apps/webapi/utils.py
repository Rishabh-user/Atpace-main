from apps.survey_questions.models import UserAnswer


def Assessment_attempt_list(attempt_list):
    details_list = []

    for test_attempt in attempt_list:
        attempt = test_attempt.test_attempet_answer.all()
        for attempt in attempt:
            details_list.append({
                "Attemp_ID": test_attempt.pk,
                "Test_Name":test_attempt.test.name,
                "Journey_Name":test_attempt.channel.title,
                "Question": attempt.question.title,
                "Answer": attempt.response,
                "Question_Marks": attempt.question_marks,
                "Given_Marks": attempt.total_marks,
                "Assessment_type":test_attempt.type,
                "User":test_attempt.user.username,
                "Time": test_attempt.created_at
            })
    return details_list

def survey_attempt_list(attempt_list):
    details_list = []
    for survey_attempt in attempt_list:
        user_answers = UserAnswer.objects.filter(survey_attempt=survey_attempt)
        for attempt in user_answers:
            details_list.append({
                "Attemp_ID": survey_attempt.id,
                "Test_Name": survey_attempt.survey.name,
                "Journey_Name": survey_attempt.survey_attempt_channel.first().channel,
                "Question": attempt.question.title,
                "Answer": attempt.response,
                "Upload_File": "" if attempt.upload_file == "" else attempt.upload_file,
                "User": survey_attempt.user.username,
                "Time": survey_attempt.created_at
            })
    return details_list


