from django.db import transaction
from django.core.management.base import BaseCommand
from apps.users.models import *
from apps.mentor.models import *
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
        mentor_obj = PoolMentor.objects.filter(pool__journey__is_active=True, is_active=True, mentor__is_active=True)
        print("Mentor count", mentor_obj.count())
        for mentor in mentor_obj:
            mentor.pool.journey.id
            mentor_response = []
            mentor_profile_assest = UserProfileAssest.objects.filter(user=mentor.mentor)
            print("Mentor count", mentor_profile_assest)
            mentor_response = [ assest.response for assest in mentor_profile_assest]
            profile = {
                "Journey": str(mentor.pool.journey.id),
                "ID": str(mentor.mentor.id),
                "Name": mentor.mentor.get_full_name(),
                "Email": mentor.mentor.email,
                "Profession": "Mentor",
                "About Us": mentor.mentor.about_us,
                "Position": mentor.mentor.position,
                "Profile Heading": mentor.mentor.profile_heading,
                "Expertize": ", ".join(str(expertize.name) for expertize in mentor.mentor.expertize.all()),
                "Industry": ", ".join(str(industry.name) for industry in mentor.mentor.industry.all()),
                "Favourite Way to Learn": mentor.mentor.favourite_way_to_learn.replace(",", ", "),
                "Interested Topic": mentor.mentor.interested_topic.replace(",", ", "),
                "Upscaling Reason": mentor.mentor.upscaling_reason.replace(",", ", "),
                "Organization": mentor.mentor.organization,
                "responses": mentor_response
            }
            print("Profile", profile)
            result = process_data(profile, "mentor", client)
            if result:
                print("mENtor email", mentor.mentor.email)
                MentorSummary.objects.get_or_create(mentor=mentor.mentor, summary=result, journey=mentor.pool.journey)
                print(f"Object was created for {mentor.mentor.email}")
            else: print(f"Record was not created for {mentor.mentor.email}")