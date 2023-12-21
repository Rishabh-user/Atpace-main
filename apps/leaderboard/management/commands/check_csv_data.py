import csv
from django.db import transaction
from django.core.management.base import BaseCommand

from apps.users.models import User

class Command(BaseCommand):
    help = "check data from csv"

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open("output.csv") as csv_file:
                reader = csv.DictReader(csv_file)
                i=0
                for row in reader:
                    i+=1 
                    print(f"row_{i}")
                    learner = User.objects.filter(id=row['Learner ID'])
                    if learner:
                        is_exist = learner.filter(userType__type__in=['Learner']).exists()
                        print(f"learner__{learner.first()}__{row['Learner ID']}: {is_exist}")
                    mentor = User.objects.filter(id=row['Matched Mentor ID'])
                    if mentor:
                        is_exist = mentor.filter(userType__type__in=['Mentor']).exists()
                        print(f"mentor__{mentor.first()}__{row['Matched Mentor ID']}: {is_exist}")
        except Exception as e:
            print(e)
        self.stdout.write(self.style.SUCCESS("All Done!"))