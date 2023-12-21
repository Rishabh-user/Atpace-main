from django.db import transaction
from django.core.management.base import BaseCommand
from apps.users.models import User, Company
from django.db.models.query_utils import Q
import csv

class Command(BaseCommand):
    help = "Collection of User without company"
    
    @transaction.atomic
    def handle(self, *args, **options):
        users = User.objects.filter(~Q(company__in=Company.objects.all()))
        fields = ["id", "userType", "full_name", "phone", "email", "is_active", "is_archive", "is_lite_signup", "is_social_login"]
        with open('without_company_users.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            for user in users:
                print(user.email)
                writer.writerow([user.id, ",".join(type.type for type in user.userType.all()), user.get_full_name(), str(user.phone), user.email, user.is_active, user.is_archive, user.is_lite_signup, user.is_social_login])
        self.stdout.write(self.style.SUCCESS("User Without Company"))