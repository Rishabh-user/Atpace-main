from django.db import transaction
from django.core.management.base import BaseCommand
from apps.users.models import UserProfileAssest, User
from apps.mentor.models import MenteeSummary
from apps.content.models import *
import boto3
import json
from apps.users.utils import invoke_endpoint, process_data
from ravinsight.settings.base import SUMMARY_ACCESS_ID, SUMMARY_ACCESS_KEY

# Initialize AWS SageMaker clients
client = boto3.client("sagemaker-runtime", aws_access_key_id=SUMMARY_ACCESS_ID,       
        aws_secret_access_key= SUMMARY_ACCESS_KEY, region_name='ap-south-1')
class Command(BaseCommand):
    help = "Update default data"

    @transaction.atomic
    def handle(self, *args, **options):
        user_channels = UserChannel.objects.filter(Channel__is_active = True, user__is_active=True)
        try:
            for user_channel in user_channels:
                user = user_channel.user
                user_profile_assest = UserProfileAssest.objects.filter(user=user, assest_question__journey=user_channel.Channel.id)
                mentee_response = [assest.response for assest in user_profile_assest]
                profile = {
                    "Journey": str(user_channel.Channel.id),
                    "ID": str(user.id),
                    "Name": user.get_full_name(),
                    "Email": user.email,
                    "Profession": "Mentee",
                    "About Us": user.about_us,
                    "Position": user.position,
                    "Profile Heading": user.profile_heading,
                    "Expertize": ", ".join(str(expertize.name) for expertize in user.expertize.all()),
                    "Industry": ", ".join(str(industry.name) for industry in user.industry.all()),
                    "Favourite Way to Learn": user.favourite_way_to_learn.replace(",", ", "),
                    "Interested Topic": user.interested_topic.replace(",", ", "),
                    "Upscaling Reason": user.upscaling_reason.replace(",", ", "),
                    "Organization": user.organization,
                    "responses": mentee_response
                }
                 
                result = process_data(profile, "mentee", client)
                if result:
                    learner = User.objects.filter(userType__type="Learner", email=user.email)
                    if learner:
                        MenteeSummary.objects.get_or_create(mentee=learner.first(), summary=result, journey=user_channel.Channel)
                        print(f"Object was created for {user.email}")
                else: print(f"Record was not created for {user.email}")
        except Exception as e:
            print(f"Record was not created for {user.email} due to {e}")
