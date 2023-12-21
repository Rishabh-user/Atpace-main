from django.urls import path
from .views import Dashboard, Learn, Activity, Mentor, Community, Goals, Support

app_name = 'learner'
urlpatterns = [
    path('dashboard/', Dashboard.as_view(), name='learner_dashboard'),
    path('learn/', Learn.as_view(), name='learner_learn'),
    path('goals/', Goals.as_view(), name='learner_goals'),
    path('activity/', Activity.as_view(), name='learner_activity'),
    path('mentor/', Mentor.as_view(), name='learner_mentor'),
    path('community/', Community.as_view(), name='learner_community'),
    path('support/', Support.as_view(), name='learner_support'),
    path('details/', Support.as_view(), name='learner_support'),
]