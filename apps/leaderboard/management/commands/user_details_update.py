from django.db import transaction
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.utils.utils import clean_text

class Command(BaseCommand):
    help = "Update default data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        user_list = User.objects.all()
        for user in user_list:
            print("before username ",user.username)
            if " " in user.username:
                username = user.username.split(" ")
                user.username = ''.join(username).lower()
                print("after username ",user.username)
            user.save()                
        self.stdout.write(self.style.SUCCESS("Username Updated!"))