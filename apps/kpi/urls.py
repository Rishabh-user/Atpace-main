from django.urls import path
from apps.kpi.api import RiskPairs, RiskMentees, RiskMentors

app_name = 'kpi'
urlpatterns = [
    path('risk-pairs/', RiskPairs.as_view(), name='risk_pairs'),
    path('risk-mentees/', RiskMentees.as_view(), name='risk_mentees'),
    path('risk-mentors/', RiskMentors.as_view(), name='risk_mentors'),
]