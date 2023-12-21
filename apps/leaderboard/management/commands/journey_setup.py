from django.db import transaction
from django.core.management.base import BaseCommand
from apps.content.models import journeyContentSetup, JourneyContentSetupOrdering

class Command(BaseCommand):
    help = "Update data"
    
    @transaction.atomic
    def handle(self, *args, **options):
        journey_content_setup_list = journeyContentSetup.objects.all()
        for setup in journey_content_setup_list:
            ordering_list = JourneyContentSetupOrdering.objects.filter(content_setup=setup).values("type")
            order_list = [value['type'] for value in ordering_list]
            if "overview" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="overview",
                    data="", display_order=1, cta_button_action='', default_order=1)
            if "learn_label" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="learn_label",
                    data="", display_order=1, cta_button_action='', default_order=1)
            if "pdpa_description" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="pdpa_description",
                    data="", display_order=1, cta_button_action='', default_order=1)
            if "pdpa_label" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="pdpa_label",
                    data="", display_order=1, cta_button_action='', default_order=1)
            if "video_url" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="video_url",
                    data="", display_order=1, cta_button_action='', default_order=1)
            if "cta_button_title" not in order_list:
                JourneyContentSetupOrdering.objects.create(content_setup=setup, journey=setup.journey, type="cta_button_title",
                    data="", display_order=1, cta_button_action='', default_order=1)
        self.stdout.write(self.style.SUCCESS("journey Content Setup Updated!"))