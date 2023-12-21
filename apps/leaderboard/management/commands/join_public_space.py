from django.db import transaction
from django.core.management.base import BaseCommand
from apps.atpace_community.models import SpaceJourney, SpaceMembers, Spaces
from apps.content.models import UserChannel
from apps.users.models import User
from apps.survey_questions.models import SurveyLabel

class Command(BaseCommand):
    help = "Update default data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        user_list = User.objects.all()
        space_list = Spaces.objects.filter.all()
        for user in user_list:
            for space in space_list:
                space_group = space.space_group
                if space.privacy == "Public":
                    if not SpaceMembers.objects.filter(user=user, space=space, space_group=space_group).exists():
                        SpaceMembers.objects.create(user=user, space=space, invitation_status="Accept",
                                                            space_group=space_group, is_joined=True, email=user.email)
                if space.privacy == "Private":
                    if space_journey := SpaceJourney.objects.get(space=space).first():
                        if UserChannel.objects.filter(user=user, Channel=space_journey.journey).exists():
                            if not SpaceMembers.objects.filter(user=user, space=space, space_group=space_group).exists():
                                SpaceMembers.objects.create(user=user, space=space, invitation_status="Accept",
                                                                    space_group=space_group, is_joined=True, email=user.email)
            self.stdout.write(self.style.SUCCESS("Space Member Created!"))