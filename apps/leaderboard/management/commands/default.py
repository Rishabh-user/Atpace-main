from django.db import transaction
from django.core.management.base import BaseCommand
from apps.users.models import ProficiencyLevel, UserTypes, User
from apps.survey_questions.models import SurveyLabel

class Command(BaseCommand):
    help = "Update default data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        try:
            label = ["Default", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
            for label in label:
                SurveyLabel.objects.create(label=label)
        except Exception as e:
            print(e)
            return(e)
        self.stdout.write(self.style.SUCCESS("Survey Label added!"))        
        try:
            label = [["Level 1", 0, 20],["Level 2", 21, 40],["Level 3", 41, 60],["Level 4", 61, 80],["Level 5", 81, 100]]
            for label in label:
                ProficiencyLevel.objects.create(level=label[0], start=label[1], end=label[2])
        except Exception as e:
            print(e)
            return(e)
        self.stdout.write(self.style.SUCCESS("Proficiency Level Added!"))
        try:
            label = ["Admin", "Learner", "Mentor", "ProgramManager", "Creator"]
            for label in label:
                UserTypes.objects.create(type=label)
        except Exception as e:
            print(e)
            return(e)
        self.stdout.write(self.style.SUCCESS("User Types Added!"))
        try:
            user_type = UserTypes.objects.get(type="Admin")
            user = User.objects.create_superuser(username="admin", email="admin@growatpace.com", password="admin", is_email_verified=True)
            user.userType.add(user_type.pk)
        except Exception as e:
            print(e)
            return(e)

        self.stdout.write(self.style.SUCCESS("Admin User Created!"))