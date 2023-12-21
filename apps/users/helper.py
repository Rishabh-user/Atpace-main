from apps.users.models import UserCompany, ProgramManager
from apps.content.models import UserChannel, Channel, UserReadContentData
from apps.mentor.models import PoolMentor
from apps.community.models import LearningJournals
from datetime import datetime, timedelta
from apps.users.models import Company, UserCompany

def user_company(user, company_id=None):
    company = user.company.all()
    if company_id:
        company = company.filter(pk=company_id)
    return company


def add_user_to_company(user, company):
    if not UserCompany.objects.filter(user=user, company=company).exists():
        UserCompany.objects.create(user=user, company=company)
    if company not in user.company.all():
        user.company.add(company)
    return True


def company_users(company, role):
    # print("role", role)
    receivers = []
    if role == "Mentee":
        user_company = UserCompany.objects.filter(company=company, user__userType__type__in=["Learner"])
        for company in user_company:
            receivers.append(company.user)
    if role == "Mentor":
        user_company = UserCompany.objects.filter(company=company, user__userType__type__in=["Mentor"])
        for company in user_company:
            receivers.append(company.user)
    if role == "Both":
        user_company = UserCompany.objects.filter(company=company, user__userType__type__in=["Learner", "Mentor"])
        for company in user_company:
            receivers.append(company.user)

    if role == "Program Manager":
        receivers = ProgramManager.objects.filter(company__in=[company], is_active=True, is_delete=False)
    return receivers


def journey_users(journey, role):
    receivers = []
    if role == "Mentee":
        user_channel = UserChannel.objects.filter(
            Channel=journey, status="Joined", user__userType__type__in=['Learner'], is_removed=False)
        print("journey function", user_channel)
        for channel in user_channel:
            receivers.append(channel.user)
    if role == "Mentor":
        print("hello mentor journey")
        pool_mentor = PoolMentor.objects.filter(pool__journey__in=[journey], is_active=True)
        print("pool mentor", pool_mentor)
        for pool in pool_mentor:
            receivers.append(pool.mentor)
    if role == "Both":
        user_channel = UserChannel.objects.filter(
            Channel=journey, status="Joined", user__userType__type__in=['Learner'], is_removed=False)
        for channel in user_channel:
            receivers.append(channel.user)
        pool_mentor = PoolMentor.objects.filter(pool__journey__in=[journey], is_active=True)
        for pool in pool_mentor:
            if pool.mentor not in receivers:
                receivers.append(pool.mentor)
    if role == "Program Manager":
        receivers = ProgramManager.objects.filter(company__in=[journey.company], is_active=True, is_delete=False)

    return receivers


def company_journey(company):
    journeys = Channel.objects.filter(company__in=[company], parent_id=None, is_active=True, is_delete=False)
    return journeys


def journal_percentage(journey):
    journals = LearningJournals.objects.filter(
        journey_id__in=[journey.id], is_draft=False, is_weekly_journal=True, updated_at__gte=datetime.now()-timedelta(days=7)).count()

    return journals


def microskill_percentage(journey):
    content = UserReadContentData.objects.filter(channel__in=[journey], status='Complete', updated_at__gte=datetime.now()-timedelta(days=7)).count()

    return content


def no_acivity_pairs(journey):

    return "0"
