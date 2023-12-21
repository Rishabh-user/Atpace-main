from django.core.management.base import BaseCommand

from apps.users.models import User, UserProfileAssest
from apps.content.models import Channel
import pandas as pd

class Command(BaseCommand):
    help = "Update default data"
    def handle(self, **options):
        try:
            data_list = []

            users = User.objects.filter(profile_assest_enable=True, is_active=True, is_archive=False, is_delete=False)

            for user in users:
                user_profile_assest = UserProfileAssest.objects.filter(user=user)
                if not user_profile_assest.count():
                    continue
                user_type = ", ".join(str(type.type) for type in user.userType.all())
                company = ", ".join(str(company.name) for company in user.company.all())
                expertize = ", ".join(str(expertize.name) for expertize in user.expertize.all())
                industry = ", ".join(str(industry.name) for industry in user.industry.all())
                for profile_assest in user_profile_assest:
                    journey_name = ''
                    if profile_assest.assest_question.journey:
                        journey = Channel.objects.filter(pk=profile_assest.assest_question.journey, parent_id=None, is_active=True, is_delete=False).first()
                        journey_name = journey.title if journey else ''
                    data_list.append([str(user.id), user.get_full_name(), user.email, user.phone, company, user_type, user.profile_heading, expertize, industry, user.favourite_way_to_learn.replace(",", ", "), user.interested_topic.replace(",", ", "), user.upscaling_reason.replace(",", ", "), user.organization, profile_assest.assest_question.question, journey_name, profile_assest.response, profile_assest.description, profile_assest.question_for])
                
            headers = ['ID', "Full Name", "Email ", "Phone", "Company", "UserType", "Profile Heading", "Expertize", "Industry", "Favourite Way to Learn", "Interested Topic", "Upscaling Reason", "Organization", "AssestQuestions", "Question Journey", "Response", "Description", "Question-For"]

            df = pd.DataFrame(data_list ,columns=headers )
            df.to_csv("UserAssestData.csv", index=False)
            print("csv done")
        except Exception as e:
            print("Error", e)   
            
# from apps.leaderboard.management.commands.csv_file
