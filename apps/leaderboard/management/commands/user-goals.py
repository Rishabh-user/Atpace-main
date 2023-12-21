import csv
from django.db import transaction
from django.core.management.base import BaseCommand
from apps.leaderboard.models import UserDrivenGoal
from apps.users.models import User


class Command(BaseCommand):
    help = "Update static data for user-goals"
    
    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open("static/csv/GoalStaticData.csv") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    try:
                        user= User.objects.get(username=row['created_by'])
                    except User.DoesNotExist:
                        return self.stdout.write("user does not exist")
                    UserDrivenGoal.objects.create(heading=row['heading'], description=row['description'], duration_number=row['duration_number'], frequency=row['frequency'],
                                         duration_time=row['duration_time'], category=row['category'], difficulty_level=row['difficulty_level'], priority_level=row['priority_level'], created_by=user)
                print(self.style.SUCCESS("Goals are created"))
        except Exception as e:
            print(self.style.ERROR("exception ",e))