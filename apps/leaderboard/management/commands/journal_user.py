from django.db import transaction
from django.core.management.base import BaseCommand

from apps.community.models import LearningJournals
from apps.users.models import User
class Command(BaseCommand):
    help = "Update user data to journal"
    
    @transaction.atomic
    def handle(self, *args, **options):
        learning_journal = LearningJournals.objects.all()
        
        for journal in learning_journal:
            try:
                journal_user = User.objects.get(email=journal.email)
                journal.user_name = f"{journal_user.first_name} {journal_user.last_name}"
                journal.user_id = journal_user.id
                journal.save()
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with {journal.email} Does Not Exist!"))
        self.stdout.write(self.style.SUCCESS("All User Updated!"))