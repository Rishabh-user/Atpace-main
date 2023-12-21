from django.db import transaction
from django.core.management.base import BaseCommand
from apps.content.models import UserChannel
from apps.users.helper import add_user_to_company

class Command(BaseCommand):
    help = "Update default data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        userchannel_list = UserChannel.objects.all()
        for user_channel in userchannel_list:
            user = user_channel.user
            journey = user_channel.Channel
            types = [type.type for type in user.userType.all()]
            if "Admin" not in types:
                add_user_to_company(user, journey.company)
        self.stdout.write(self.style.SUCCESS("User Company Updated!"))