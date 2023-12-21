from os import name
from django.urls import path
from apps.community.views import (AllWeeklyJournals, AskKeyPoint, AskQuestion, JourneyPost, JourneyPostDetails, PostAnswer, LearningJournal,
                                  AddLearningJournal, EditJournal, PostJournal, AllJournal, AllWeeklyJournalsList, AllLearningJournal, WeekelyJournals, EditWeeklyJournals,  CreateJournalTemplates, JournalTemplateslList, JournalTemplateslUpdate, delete_attachment)

app_name = 'community'


urlpatterns = [
    path('ask-key-point/<uuid:content>/<uuid:group>', AskKeyPoint.as_view(), name="ask_key_point"),
    path('ask-question/', AskQuestion.as_view(), name="ask_question"),
    path('add_learning_journal', AddLearningJournal.as_view(), name="add_learning_journal"),
    path('community-post/<uuid:channel>', JourneyPost.as_view(), name="journey_post"),
    path('learning-journal/<uuid:channel>', LearningJournal.as_view(), name="learning_journal"),
    path('all-learning-journal/', AllLearningJournal.as_view(), name="all_learning_journal"),
    path('all-journal/', AllJournal.as_view(), name="all_journal"),
    path('all-journal/<str:pk>/', AllJournal.as_view(), name="all_journal_with_id"),
    path('post-journal/', PostJournal.as_view(), name="post_journal"),
    path('edit-journal/<uuid:user_id>/<int:pk>/', EditJournal.as_view(), name="edit_journal"),



    path('joureny-post-details/<uuid:channel>/<uuid:post_id>', JourneyPostDetails.as_view(), name="journey_post_details"),
    path('post-answer/', PostAnswer.as_view(), name="post_answer"),
    path('weekly-journal/<int:pk>', WeekelyJournals.as_view(), name="weekly_journals"),
    path('edit-weekly-journal/<int:id>', EditWeeklyJournals.as_view(), name="edit_weekly_journals"),
    path('all-weekly-journal/', AllWeeklyJournals.as_view(), name="all_weekly_journals"),
    path("all_weekly_journal_list", AllWeeklyJournalsList.as_view(), name="all_weekly_journal_list"),
    path('create-journals-template/', CreateJournalTemplates.as_view(), name="create_journal_template"),
    path('update-journals-template/<int:pk>', JournalTemplateslUpdate.as_view(), name="update_journal_template"),
    path('templates-list/', JournalTemplateslList.as_view(), name="journals_templates_list"),
    path('delete-attachment/<uuid:attachment_id>/', delete_attachment, name="delete_attachment"),
]