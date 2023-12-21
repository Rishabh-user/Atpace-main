from django.core import files
from django.core.files.base import ContentFile
import boto3, requests
from io import BytesIO
from ravinsight.settings.base import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME
from PIL import Image, ImageDraw, ImageFont
from datetime import *
import math, json, ast
from apps.atpace_community.models import SpaceJourney, Post
from apps.mentor.models import mentorCalendar, PoolMentor, AssignMentorToUser
from apps.atpace_community.utils import aware_time
from apps.community.models import LearningJournals, WeeklyLearningJournals
from apps.survey_questions.models import Survey, SurveyLabel
from apps.test_series.models import TestSeries
from apps.users.models import Company, ProfileAssestQuestion, User, Collabarate
from .models import CertificateTemplate, Channel, ChannelGroupContent, ContentData, JourneyContentSetupOrdering, ProgramTeamAnnouncement, PublicProgramAnnouncement, SkillConfig, SurveyChannel, SkillConfigLevel, ContentChannels,  UserChannel, UserCourseStart, CertificateSignature, UserCertificate, journeyContentSetup
from django.db.models import Q
from ravinsight.settings import BASE_DIR
from apps.content.models import UserCourseStart, Channel, MentoringJourney, Content, TestAttempt, ChannelGroupContent, ChannelGroup, UserChannel


def is_parent_channel(channel_id):
    channel = Channel.objects.get(pk=channel_id)
    try:
        if channel.parent_id is None:
            channel_id = channel.pk
            is_community_required = channel.is_community_required
            channel = channel
        else:
            channel_id = channel.parent_id.pk
            is_community_required = channel.parent_id.is_community_required
            channel = channel.parent_id
    except Exception:
        channel_id = channel.pk
        is_community_required = channel.is_community_required
        channel = channel

    return {"channel_id": channel_id, "channel": channel, "is_community_required": is_community_required}


def public_channel_list(user, company_id=None):
    if company_id is None:
        company = user.company.all()
    else:
        company = user.company.filter(pk=company_id)

    channels = Channel.objects.filter(Q(is_global=True) | Q(company__in=company), closure_date__gt=datetime.now(),
                                      parent_id=None, is_active=True, is_delete=False)
    channel = ''
    browse_channel = []
    for channels in channels:
        if channels.channel_type == "SurveyCourse":
            if channels.survey is not None:
                
                channel = channels
                browse_channel.append({
                    "channel": channel,
                    "status": check_journey_complete_status(user, channel)
                })
        elif channels.channel_type in ["onlyCommunity", "Course", "MentoringJourney", "SkillDevelopment"]:
            channel = channels
            browse_channel.append({
                "channel": channel,
                "status": check_journey_complete_status(user, channel)
            })

    return browse_channel


def check_journey_complete_status(user, channel):
    try:
        UserChannel.objects.get(user=user, Channel=channel, is_completed=True, Channel__closure_date__gt=datetime.now())
        complete_status = 'completed'

    except:
        complete_status = ""
    return complete_status

def public_channel_list_search(user, search, company_id=None):

    # company = user.company.filter()
    channels_list = Channel.objects.filter(closure_date__gt=datetime.now(), title__icontains=search)
    channels = channels_list.filter(Q(is_global=True) | Q(company__id=company_id),
                                    parent_id=None, is_active=True, is_delete=False, )

    channel = []
    for channels in channels:
        if channels.channel_type == "SurveyCourse":
            if channels.survey is not None:
                channel.append(channels)
        elif channels.channel_type in ["onlyCommunity", "Course", "MentoringJourney", "SkillDevelopment"]:
            channel.append(channels)
    return channel


def get_display_content(channel, channel_group, user):
    display_content = []
    channel_content = ChannelGroupContent.objects.filter(channel_group__in=channel_group, status="Live", is_delete=False)
    for channel_content in channel_content:
        read_content = channel_content.content
        try:
            user_read_status = UserCourseStart.objects.get(
                user=user, content=read_content, channel_group=channel_content.channel_group, channel=channel.pk)
            read_status = user_read_status.status
        except UserCourseStart.DoesNotExist:
            read_status = ""

        display_content.append({

            "type": "quest",
            "title": read_content.title,
            "image": read_content.image,
            "id": read_content.id,
            "channel_group": channel_content.channel_group.pk,
            "journey_id": channel.pk,
            "read_status": read_status
        })
    return display_content


def Journey(channel, user):
    try:
        user_channel = UserChannel.objects.get(Channel=channel, user=user, Channel__closure_date__gt=datetime.now(), status="Joined")
    except UserChannel.DoesNotExist:
        return False
    return True


def change_course_status_in_group(content, status="Pending"):
    update_status = ChannelGroupContent.objects.filter(content=content, is_delete=False).update(status=status)
    return bool(update_status)

def public_announcement_list(company=None, journey=None):
    public_announcements = PublicProgramAnnouncement.objects.all()
    if company is not None:
        public_announcements = public_announcements.filter(journey__closure_date__gt=datetime.now(), journey__company=company)
    if journey is not None:
        user_journey_list = [channel.Channel for channel in journey]
        public_announcements = public_announcements.filter(journey__in=user_journey_list)
    announcement_list = []
    for announcement in public_announcements:
        topic_for = None; image = None; journey_group = None; skill_id = None
        if announcement.type == "MicroSkill":
            topic_for = Content.objects.filter(pk=announcement.topic_id, is_delete=False).first()
            if topic_for:
                topic_name = topic_for.title
                id = topic_for.id
                image = announcement.cover_image.url if announcement.cover_image else topic_for.image.url
                journey_group = announcement.channel_group
                skill_id = announcement.skill_id
        elif announcement.type == "Journey":
            topic_for = announcement.journey
            topic_name = announcement.journey.title
            id = announcement.journey.id
            image = announcement.cover_image.url if announcement.cover_image else announcement.journey.image.url
        elif announcement.type == "ProfileAssessment":
            topic_for = ProfileAssestQuestion.objects.filter(pk=announcement.topic_id, is_delete=False).first()
            if topic_for:
                topic_name = topic_for.question
                id = topic_for.pk
                image = announcement.cover_image.url
        elif announcement.type == "Survey":
            topic_for = Survey.objects.filter(pk=announcement.topic_id, is_delete=False).first()
            if topic_for:
                topic_name = topic_for.name
                id = topic_for.id
                image = announcement.cover_image.url if announcement.cover_image else topic_for.cover_image.url
        elif announcement.type == "MentoringJournals":
            topic_for = WeeklyLearningJournals.objects.filter(pk=announcement.topic_id).first()
            if topic_for:
                topic_name = topic_for.name
                id = topic_for.id
                image = announcement.cover_image.url if announcement.cover_image else ''
        elif announcement.type == "ProgramAnnouncement":
            topic_for = announcement.journey
            topic_name = announcement.journey.title
            id = announcement.journey.id
            image = announcement.cover_image.url if announcement.cover_image else announcement.journey.image.url
        announcement_list.append({
            "id": announcement.id,
            "company_id": announcement.company.id,
            "company_name": announcement.company.name,
            "journey_id": announcement.journey.id,
            "journey_name": announcement.journey.title,
            "journey_type": announcement.journey.channel_type,
            "journey_group": journey_group,
            "skill_id": skill_id,
            "type": announcement.type,
            "topic": announcement.topic,
            "summary": announcement.summary,
            "topic_name": '' if not topic_for else topic_name,
            "topic_id": '' if not topic_for else id,
            "topic_image": image,
            "is_active": announcement.is_active,
            "created_at": announcement.announce_date if announcement.announce_date else ''
        })
    return announcement_list


def company_journeys(user_type, user, company_id=None):
    company = []
    if user_type != 'Admin':
        company = user.company.all()
    else:
        company = Company.objects.all()
    if company_id:
        company = user.company.filter(pk=company_id)

    journey = Channel.objects.filter(company__in=company, closure_date__gt=datetime.now(),
                                      parent_id=None, is_active=True, is_delete=False)

    return journey

def day_compare(read_status, channel, ago_time, course_start=None):
    if read_status != "Complete" and course_start.updated_at < aware_time(
        ago_time
    ):
        return channel
    return None

def weekly_quest_learn(user, ago_time, company):
    user_channel = UserChannel.objects.filter(user=user, status="Joined", Channel__company=company, is_removed=False, is_completed=False)
    journey_list = []
    content_list = []
    all_content = 0
    for journey in user_channel:
        channel = journey.Channel
        course_start = ""
        channel_group = ChannelGroup.objects.filter(channel=channel, is_delete=False)
        if channel.channel_type == "SkillDevelopment":
            if channel.is_test_required:
                assessment_attempt = TestAttempt.objects.filter(
                    user=user, channel=channel, test=channel.test_series)
                if len(assessment_attempt) > 0:
                    assessment_attempt = assessment_attempt.first()

                    try:
                        assessment_attempt_marks = math.ceil(
                            (assessment_attempt.total_marks / assessment_attempt.test_marks) * 100)

                    except:
                        assessment_attempt_marks = assessment_attempt.total_marks

                    channel_group = channel_group.filter(
                        start_mark__lte=assessment_attempt_marks, end_marks__gte=assessment_attempt_marks)
                else:
                    channel_group = []
            else:
                assessment_attempt = TestAttempt.objects.filter(
                    user=user, channel=channel, test=channel.test_series)

                level = "Level 1"
                if len(assessment_attempt) > 0:
                    assessment_attempt = assessment_attempt.first()
                    level = assessment_attempt.user_skill

                level = SurveyLabel.objects.get(label=level)

                channel_group = channel_group.filter(channel_for=level)
            for channel_group in channel_group:
                channel_group_content = ChannelGroupContent.objects.filter(channel_group=channel_group, content__status="Live", is_delete=False)
                all_content = channel_group_content.count()
                for channel_group_content in channel_group_content:
                    course_start = UserCourseStart.objects.filter(
                        user=user, content=channel_group_content.content, channel_group=channel_group, channel=channel).first()
                    if course_start is not None:
                        read_status = course_start.status
                    if course_start:
                        if day_compare(read_status, channel, ago_time, course_start) and day_compare(read_status, channel, ago_time, course_start) not in journey_list:
                            journey_list.append(channel)
                            content_list.append(channel_group_content.content)

        elif channel.channel_type == "MentoringJourney":
            journey_group = ChannelGroup.objects.filter(channel=channel, is_delete=False).first()
            mentoring_journey = MentoringJourney.objects.filter(journey=channel, journey_group=journey_group, meta_key="quest", is_delete=False)
            all_content = mentoring_journey.count()
            for mentoring_journey in mentoring_journey:
                read_status = ""
                content = Content.objects.get(pk=mentoring_journey.value)
                try:
                    course_start = UserCourseStart.objects.get(
                        user=user, content=content, channel_group=mentoring_journey.journey_group, channel=channel.pk)
                    read_status = course_start.status
                except UserCourseStart.DoesNotExist:
                    read_status = ""
                if course_start:
                    if day_compare(read_status, channel, ago_time, course_start) and day_compare(read_status, channel, ago_time, course_start) not in journey_list:
                        journey_list.append(channel)
                        content_list.append(content)
    return journey_list, len(content_list), all_content

def learn_journal(user, ago_time, company):
    user_channel = UserChannel.objects.filter(user=user, Channel__company=company, status="Joined", is_removed=False, is_completed=False, Channel__channel_type="MentoringJourney")
    learnig_journals_list = []
    learnig_journals = []
    for journey in user_channel:
        channel = journey.Channel
        journey_group = ChannelGroup.objects.filter(channel=channel, is_delete=False).first()
        mentoring_journey = MentoringJourney.objects.filter(journey=channel, journey_group=journey_group, is_delete=False)
        for mentoring_journey in mentoring_journey:
            type = mentoring_journey.meta_key
            if type == "journals":
                weekely_journals = WeeklyLearningJournals.objects.get(pk=mentoring_journey.value, journey_id=channel.pk)
                learnig_journals = LearningJournals.objects.filter(is_draft=True, weekely_journal_id=weekely_journals.pk, journey_id=channel.pk, email=user.email, updated_at__gte=ago_time)
                if learnig_journals.count() > 0:
                    for journal in learnig_journals:
                        learnig_journals_list.append({"journal_id": journal.id, "title": weekely_journals.name})
    return learnig_journals_list, len(learnig_journals)

def user_calls(user, ago_time, company):
    mentor_cal = mentorCalendar.objects.filter(participants__in=[user], company=company, start_time__gte=ago_time, slot_status="Booked")
    total_calls = mentor_cal.count() or 0
    complete_calls = mentor_cal.filter(status="Completed").count() or 0
    no_calls = total_calls - complete_calls
    collaborates = Collabarate.objects.filter(Q(participants__in=[user]), is_active=True, is_cancel=False, company=company, updated_at__gte=ago_time).count()
    if isinstance(complete_calls, int) and isinstance(collaborates, int):
        return complete_calls+collaborates, no_calls, total_calls+collaborates
    elif isinstance(complete_calls, int):
        return complete_calls, no_calls, total_calls
    elif isinstance(collaborates, int):
        return collaborates, no_calls, collaborates
    return 0, no_calls, total_calls+collaborates

def user_posts(user, ago_time, company):
    user_channel = UserChannel.objects.filter(user=user, Channel__company=company, status="Joined", is_removed=False, is_completed=False, Channel__channel_type="MentoringJourney")
    all_post = []
    for channel in user_channel:
        journey = channel.Channel
        if journey.is_community_required:
            space_journey = SpaceJourney.objects.filter(journey=journey).first()
            all_post = Post.objects.filter(created_by=user, space=space_journey.space,
                    is_active=True, is_delete=False, updated_at__gte=ago_time)
        
    return len(all_post)

def mentor_journal(user, company, ago_time):
    pool_mentor = PoolMentor.objects.filter(mentor=user, pool__company=company)
    journey_list = [pool.pool.journey for pool in pool_mentor]
    learnig_journals_list=[]
    learnig_journals = []
    for journey in journey_list:
        journey_group = ChannelGroup.objects.filter(channel=journey, is_delete=False).first()
        mentoring_journey = MentoringJourney.objects.filter(journey=journey, journey_group=journey_group, meta_key="journals", is_delete=False)
        for mentoring_journey in mentoring_journey:
            weekely_journals = WeeklyLearningJournals.objects.get(pk=mentoring_journey.value, journey_id=journey.pk)
            learnig_journals = LearningJournals.objects.filter(is_draft=True, weekely_journal_id=weekely_journals.pk, journey_id=journey.pk, email=user.email, updated_at__gte=ago_time)
            if learnig_journals.count() > 0:
                for journal in learnig_journals:
                    learnig_journals_list.append({"journal_id": journal.id, "title": weekely_journals.name})
    return learnig_journals_list, len(learnig_journals)

def mentor_quest(user, company, ago_time):
    pool_mentor = PoolMentor.objects.filter(mentor=user, pool__company=company)
    user_journey_list = [pool.pool.journey for pool in pool_mentor]
    content_list = []
    journey_list = []
    all_content = 0
    for channel in user_journey_list:
        journey_group = ChannelGroup.objects.filter(channel=channel, is_delete=False).first()
        mentoring_journey = MentoringJourney.objects.filter(journey=channel, journey_group=journey_group, meta_key="quest", is_delete=False)
        all_content = mentoring_journey.count()
        for mentoring_journey in mentoring_journey:
            read_status = ""
            content = Content.objects.get(pk=mentoring_journey.value)
            course_start = None
            try:
                course_start = UserCourseStart.objects.get(
                    user=user, content=content, channel_group=mentoring_journey.journey_group, channel=channel.pk)
                read_status = course_start.status
            except UserCourseStart.DoesNotExist:
                read_status = ""
            if course_start:
                if day_compare(read_status, channel, ago_time, course_start) and day_compare(read_status, channel, ago_time, course_start) not in journey_list:
                    journey_list.append(channel)
                    content_list.append(content)
    return journey_list, len(content_list), all_content

def mentor_calls(user, company, ago_time):
    mentor_cal = mentorCalendar.objects.filter(mentor=user, company=company, start_time__gte=ago_time, slot_status="Booked")
    total_calls = mentor_cal.count() or 0
    complete_calls = mentor_cal.filter(status="Completed").count() or 0
    no_calls = total_calls - complete_calls
    collaborates = Collabarate.objects.filter(Q(participants__in=[user]) | Q(speaker=user), is_active=True, is_cancel=False, company=company, updated_at__gte=ago_time).count()
    if isinstance(complete_calls, int) and isinstance(collaborates, int):
        return complete_calls+collaborates, no_calls, total_calls+collaborates
    elif isinstance(complete_calls, int):
        return complete_calls, no_calls, total_calls
    elif isinstance(collaborates, int):
        return collaborates, no_calls, collaborates
    return 0, no_calls, total_calls

def replicate_profile_assessment(journey_id, copy_journey_id):
    profile_assessment = ProfileAssestQuestion.objects.filter(journey=journey_id)
    for assessment in profile_assessment:
        assessment.pk = None
        assessment.journey = copy_journey_id
        assessment.save()
    return True

def get_file_name(url):
    return url.split("?")[0].split(".com/")[1]

def update_db(user, journey, certificate, ):
    pass

def s3_image_read(key):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    file_byte_string = s3.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=key)['Body'].read()
    return BytesIO(file_byte_string)

# new function that generates cert for 2 and 3 signatures
def user_certificate_update(file, user_id, user_name, role, journey_title, from_till_date, name1, headline1, signature1, name2, headline2, signature2, name3, headline3, signature3, user_type_role = None):
    user_name = user_name 
    names = f"{user_name.split(' ')[0]}.png"
    im = Image.open(s3_image_read(file))

    d = ImageDraw.Draw(im)
    w, h = im.size
    user_name_coordinates = (w/2, 550)
    role = role
    # if user_type_role.lower() == "learner": role = "Intern"
    # elif user_type_role.lower() == "mentor": role = "Mentor"
    # elif user_type_role.lower() == "programmanager": role = "Manager"

    journey_coordinates = (w/2, 740)
    role_as_coordinates = (w/2,775 )
    role_coordinates = (w/2, 810)
    from_till_date_coordinates = (w/2, 850)

    sign_size = (400,300)

    text_color = (255, 255, 255)

    journey_title = journey_title
    user_name_font = ImageFont.truetype(f"static/roman_2.ttf", 150)
    journey_font = ImageFont.truetype(f"static/roman_2.ttf", 50)
    date_font = ImageFont.truetype(f"static/roman_2.ttf", 25)
    role_font = ImageFont.truetype(f"static/roman_2.ttf", 40)
    name_font = ImageFont.truetype(f"static/Roman2.ttf", 30)
    designation_font = ImageFont.truetype(f"static/Roman2.ttf", 25)

    from_till_date = from_till_date
    name1 = name1
    headline1 = headline1
    name2 = name2
    headline2 = headline2
    name3 = name3
    headline3 = headline3

    d.text(user_name_coordinates, user_name, fill = text_color, font = user_name_font, align="center", anchor="mm")
    d.text(role_coordinates, role, fill = text_color, font = role_font, align="center", anchor="mm")
    d.text(role_as_coordinates, "as", fill = text_color, font = designation_font, align="center", anchor="mm")
    d.text(journey_coordinates, journey_title, fill = text_color, font = journey_font, align="center", anchor="mm")
    d.text(from_till_date_coordinates, f"from {from_till_date}", fill = text_color, font = date_font, align="center", anchor="mm")

    if name1 and name2 and name3:
        
        sign1 = Image.open(requests.get(signature1, stream=True).raw)
        sign2 = Image.open(requests.get(signature2, stream=True).raw)
        sign3 = Image.open(requests.get(signature3, stream=True).raw)
        # sign2 = Image.open(f"{BASE_DIR}/static/signature.png")
        # sign3 = Image.open(f"{BASE_DIR}/static/signature.png")

        sign1.resize(sign_size, Image.ANTIALIAS)
        sign2.resize(sign_size, Image.ANTIALIAS)
        sign3.resize(sign_size, Image.ANTIALIAS)

        sign_coordinates1 = (int(w/13), 940)
        name_coordinates1 = (w/6,1130)
        headline_coordinates1 = (w/6,1160)

        sign_coordinates2 = (int(w/2.57), 940)
        name_coordinates2 = (w/2.05,1130)
        headline_coordinates2 = (w/2.05,1160)

        sign_coordinates3 = (int(5.75*w/8), 938)
        name_coordinates3 = (5*w/6.1,1130)
        headline_coordinates3 = (5*w/6.1,1160)

        im.paste(sign1, sign_coordinates1, sign1)
        im.paste(sign2, sign_coordinates2, sign2)
        im.paste(sign3, sign_coordinates3, sign3)

        d.text(name_coordinates1, name1, fill = text_color, font = name_font, align="center", anchor="mm")
        d.text(headline_coordinates1, headline1, fill = text_color, font = designation_font, align="center", anchor="mm")
        d.text(name_coordinates2, name2, fill = text_color, font = name_font, align="left", anchor="mm")
        d.text(headline_coordinates2, headline2, fill = text_color, font = designation_font, align="left", anchor="mm")
        d.text(name_coordinates3, name3, fill = text_color, font = name_font, align="center", anchor="mm")
        d.text(headline_coordinates3, headline3, fill = text_color, font = designation_font, align="center", anchor="mm")

    elif name1 and name2:       
        sign1 = Image.open(requests.get(signature1, stream=True).raw)
        sign2 = Image.open(requests.get(signature2, stream=True).raw)

        sign1.resize(sign_size, Image.ANTIALIAS)
        sign2.resize(sign_size, Image.ANTIALIAS)
        
        sign_coordinates1 = (int(w/8.5), 920)
        name_coordinates1 = (w/4.65,1110)
        headline_coordinates1 = (w/4.65,1140)

        sign_coordinates2 = (int(w/1.4939), 922)
        name_coordinates2 = (w/1.3,1110)
        headline_coordinates2 = (w/1.3,1140)

        im.paste(sign1, sign_coordinates1, sign1)
        im.paste(sign2, sign_coordinates2, sign2)

        d.text(name_coordinates1, name1, fill = text_color, font = name_font, align="center", anchor="mm")
        d.text(headline_coordinates1, headline1, fill = text_color, font = designation_font, align="center", anchor="mm")
        d.text(name_coordinates2, name2, fill = text_color, font = name_font, align="left", anchor="mm")
        d.text(headline_coordinates2, headline2, fill = text_color, font = designation_font, align="left", anchor="mm")

    return im, names


def generate_certificate(user_id, user_name, journey_id, user_type_role=None):
    try:
        certificate_template = CertificateTemplate.objects.get(journey__id=journey_id, is_active=True, is_delete=False)
    except CertificateTemplate.DoesNotExist:
        return False
    
    base_url = "https://atpace-storage.s3.amazonaws.com/"
    user = User.objects.get(id=user_id)
    authourizer_signature = CertificateSignature.objects.filter(certificate_template=certificate_template).order_by('created_at')
    file = get_file_name(certificate_template.file.url)
    authorizer = []
    i = 0
    for sign in authourizer_signature:
        i+=1
        authorizer.append({f"name{i}": sign.name, f"headline{i}": sign.headline, f"signature{i}": sign.sign.url})
        
    name1=authorizer[0]['name1']
    headline1=authorizer[0]['headline1']
    signature1=get_file_name(authorizer[0]['signature1'])

    name2=authorizer[1]['name2']
    headline2=authorizer[1]['headline2']
    signature2=get_file_name(authorizer[1]['signature2'])

    try:
        name3=authorizer[2]['name3']
        headline3=authorizer[2]['headline3']
        signature3=get_file_name(authorizer[2]['signature3'])
        signature1 = base_url + signature1
        signature2 = base_url + signature2
        signature3 = base_url + signature3
    except:
        name3, headline3, signature3 = None, None, None
        signature1 = base_url + signature1
        signature2 = base_url + signature2
    
    try:
        role_obj = ast.literal_eval(certificate_template.role)
        if user_type_role == "ProgramManager": role = role_obj['ProgramManager']
        elif user_type_role == "Mentor": role = role_obj['Mentor']
        elif user_type_role == "Learner": role = role_obj['Learner']
        else: return False
    except Exception as e:
        print("Error in role object", e)
        role = certificate_template.role

    certificate, names = user_certificate_update(file, str(user_id), user_name, role, certificate_template.journey_title, certificate_template.from_till_date, name1, headline1, signature1, name2, headline2, signature2, name3, headline3, signature3)
    
    user = User.objects.get(pk=user_id)
    user_certificate = UserCertificate.objects.create(journey=certificate_template.journey, company=certificate_template.company, user=user, certificate_template=certificate_template)
    print("User certificate created")
    image_file = BytesIO()
    certificate.save(image_file, 'PNG')
    print("Certificate saved in the model")
    user_certificate.file.save(names, files.File(image_file), save=True)
    file_url = user_certificate.file.url
    print(f"Certificate_url: {user_certificate.file.url}")
    return file_url


def replicate_journey_content(journey_id, copy_journey, channel_group, user):
    # print("replicate journey ",journey_id, copy_journey, channel_group, user)
    mentoring_journey = MentoringJourney.objects.filter(
                    journey__id=journey_id, is_delete=False).order_by('display_order')
    # print("mentoring_journey", mentoring_journey)
    for mentoring_journey in mentoring_journey:
        mentoring_journey_copy =  mentoring_journey

        mentoring_journey_copy.pk = None
        mentoring_journey_copy.journey = copy_journey
        mentoring_journey_copy.journey_group = channel_group
        mentoring_journey_copy.created_by = user.pk
        mentoring_journey_copy.save()

    # for journey_content in mentoring_journey:
    #     if journey_content.meta_key == 'quest':
    #         content = Content.objects.get(pk=journey_content.value)
        
    #     if journey_content.meta_key == 'assessment':
    #         assessment = TestSeries.objects.get(pk=journey_content.value)

    #     if journey_content.meta_key == 'survey':
    #         survey = Survey.objects.get(pk=journey_content.value)

    #     if journey_content.meta_key == 'journals':
    #         journal = LearningJournals.objects.get(pk=journey_content.value)
            

    return True


def replicate_journey_content_setup(journey_id, copy_journey, user):
    content_setup_journey = journeyContentSetup.objects.filter(journey__id=journey_id).first()
    content_setup_order = JourneyContentSetupOrdering.objects.filter(content_setup=content_setup_journey)
    if content_setup_journey:
        content_setup_copy = content_setup_journey
        content_setup_copy.pk = None
        content_setup_copy.journey = copy_journey
        content_setup_copy.created_by = user
        content_setup_copy.save()

        for setup_order in content_setup_order:
            setup_order_copy = setup_order
            setup_order_copy.pk = None
            setup_order_copy.content_setup = content_setup_copy
            setup_order_copy.journey = copy_journey
            setup_order_copy.save()

    return True

def replicate_skill_journey_data(channel, journey_name, user):
    survey_level = SurveyLabel.objects.filter(label="Default").first()
    channel_group = ChannelGroup.objects.filter(title="Default", channel=channel, channel_for=survey_level).first()
    channel_group_content = ChannelGroupContent.objects.filter(channel_group=channel_group)
    survey_channel= SurveyChannel.objects.filter(channel=channel)
    content_channel = ContentChannels.objects.filter(Channel=channel)

    journey = channel
    journey.pk = None
    journey.title = journey_name
    journey.created_by = user
    journey.save()

    channel_group_copy = ChannelGroup.objects.create(title="Default", channel=journey, channel_for=survey_level)

    for group_content in channel_group_content:
        channel_group_content_copy = group_content
        channel_group_content_copy.pk = None
        channel_group_content_copy.channel_group = channel_group_copy
        channel_group_content_copy.save()

    for survey in survey_channel:
        survey_channel_copy = survey
        survey_channel_copy.pk = None
        survey_channel_copy.channel = journey
        survey_channel_copy.save()

    for content in content_channel:
        content_channel_copy = content
        content_channel_copy.pk = None
        content_channel_copy.Channel = journey
        content_channel_copy.save()
    
    return journey, channel_group_copy


def replicate_skill_data(channel, journey_copy, channel_group_copy, skill_config, user): #channel=skill
    survey_channel= SurveyChannel.objects.filter(channel=channel)
    content_channel = ContentChannels.objects.filter(Channel=channel)
    channel_group = ChannelGroup.objects.filter(channel=channel)

    if skill_config:
        journey_skill_config = skill_config.filter(sub_channel=channel).first()
        skill_config_level = SkillConfigLevel.objects.filter(skill_config=journey_skill_config)

        skill_config_copy = journey_skill_config
        skill_config_copy.pk = None
        skill_config_copy.channel = journey_copy
        skill_config_copy.sub_channel = channel
        skill_config_copy.channel_group = channel_group_copy
        skill_config_copy.save()

        for level in skill_config_level:
            skill_config_level_copy = level
            skill_config_level_copy.pk = None
            skill_config_level_copy.skill_config = skill_config_copy
            skill_config_level_copy.channel_group = channel_group_copy
            skill_config_level_copy.save()
    

    journey = channel
    journey.pk = None
    journey.parent_id = journey_copy
    journey.created_by = user
    journey.save()

    for group in channel_group:
        print("group", group)
        channel_group_content = ChannelGroupContent.objects.filter(channel_group=group)
        skill_config_level = SkillConfigLevel.objects.filter(channel_group=group)
        print("skill_config_level", skill_config_level, skill_config_level.count())

        channel_group_copy = group
        channel_group_copy.pk = None
        channel_group_copy.channel = journey
        channel_group_copy.save()

        for group_content in channel_group_content:
            channel_group_content_copy = group_content
            channel_group_content_copy.pk = None
            channel_group_content_copy.channel_group = channel_group_copy
            channel_group_content_copy.save()


    for survey in survey_channel:
        survey_channel_copy = survey
        survey_channel_copy.pk = None
        survey_channel_copy.channel = journey
        survey_channel_copy.save()

    for content in content_channel:
        content_channel_copy = content
        content_channel_copy.pk = None
        content_channel_copy.Channel = journey
        content_channel_copy.save()

    return True



# old function that generates cert for 3 signatures
# def user_certificate_update(file, user_id, user_name, role, journey_title, from_till_date, name1, headline1, signature1, name2, headline2, signature2, name3, headline3, signature3):
#     user_name = user_name 
#     names = f"{user_name.split(' ')[0]}.png"
#     im = Image.open(s3_image_read(file))
#     d = ImageDraw.Draw(im)
#     w, h = im.size
#     # width = (w-len(user_name))/2
#     user_name_coordinates = (w/2, 550)
#     role = role

#     role_coordinates = (w/2, 735)
#     role_for_coordinates = (w/2, 775)
#     journey_coordinates = (w/2, 810)
#     from_till_date_coordinates = (w/2, 855)

#     sign_coordinates1 = (int(w/13), 920)
#     name_coordinates1 = (w/6,1150)
#     headline_coordinates1 = (w/6,1175)

#     sign_coordinates2 = (int(w/2.5), 920)
#     name_coordinates2 = (w/2,1150)
#     headline_coordinates2 = (w/2,1175)

#     sign_coordinates3 = (int(5.8*w/8), 920)
#     name_coordinates3 = (5*w/6,1150)
#     headline_coordinates3 = (5*w/6,1175)
#     text_color = (255, 255, 255)

#     sign_size = (400,300)

#     text_color = (255, 255, 255)
#     sign1 = Image.open(f"{BASE_DIR}/static/signature.png")
#     sign2 = Image.open(f"{BASE_DIR}/static/signature.png")
#     sign3 = Image.open(f"{BASE_DIR}/static/signature.png")

#     # sign1.thumbnail(sign_size, Image.ANTIALIAS)
#     # sign2.thumbnail(sign_size, Image.ANTIALIAS)
#     # sign3.thumbnail(sign_size, Image.ANTIALIAS)
#     sign1.resize(sign_size, Image.ANTIALIAS)
#     sign2.resize(sign_size, Image.ANTIALIAS)
#     sign3.resize(sign_size, Image.ANTIALIAS)

#     journey_title = journey_title
#     user_name_font = ImageFont.truetype(f"static/roman_2.ttf", 150)
#     journey_font = ImageFont.truetype(f"static/roman_2.ttf", 50)
#     date_font = ImageFont.truetype(f"static/roman_2.ttf", 25)
#     role_font = ImageFont.truetype(f"static/roman_2.ttf", 40)
#     name_font = ImageFont.truetype(f"static/Roman2.ttf", 30)
#     designation_font = ImageFont.truetype(f"static/Roman2.ttf", 25)

#     from_till_date = from_till_date
#     name1 = name1
#     headline1 = headline1
#     name2 = name2
#     headline2 = headline2
#     name3 = name3
#     headline3 = headline3

#     im.paste(sign1, sign_coordinates1, sign1)
#     im.paste(sign2, sign_coordinates2, sign2)
#     im.paste(sign3, sign_coordinates3, sign3)

#     d.text(user_name_coordinates, user_name, fill = text_color, font = user_name_font, align="center", anchor="mm")
#     d.text(role_coordinates, role, fill = text_color, font = role_font, align="center", anchor="mm")
#     d.text(role_for_coordinates, "for", fill = text_color, font = designation_font, align="center", anchor="mm")
#     d.text(journey_coordinates, journey_title, fill = text_color, font = journey_font, align="center", anchor="mm")
#     d.text(from_till_date_coordinates, from_till_date, fill = text_color, font = date_font, align="center", anchor="mm")
#     d.text(name_coordinates1, name1, fill = text_color, font = name_font, align="center", anchor="mm")
#     d.text(headline_coordinates1, headline1, fill = text_color, font = designation_font, align="center", anchor="mm")
#     d.text(name_coordinates2, name2, fill = text_color, font = name_font, align="left", anchor="mm")
#     d.text(headline_coordinates2, headline2, fill = text_color, font = designation_font, align="left", anchor="mm")
#     d.text(name_coordinates3, name3, fill = text_color, font = name_font, align="center", anchor="mm")
#     d.text(headline_coordinates3, headline3, fill = text_color, font = designation_font, align="center", anchor="mm")

#     return im, names
