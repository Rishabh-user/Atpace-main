from datetime import datetime
from apps.content.models import Channel
from apps.users.helper import user_company


def obj_image(obj):
    if obj.image:
        avatar = str(obj.image.url)
        avatar = avatar.split('?')
        return avatar[0]
    else:
        return ''

def journey_params(journey_id):
    if not journey_id:
        return None
    journey = Channel.objects.filter(id=journey_id, is_active=True, is_delete=False, parent_id=None, closure_date__gt=datetime.now()).first()
    return journey.title

def program_manager_journey_list(user, company_id=None):
    company_list = user_company(user, company_id)

    return Channel.objects.filter(parent_id=None, is_active=True, is_delete=False, company__in=company_list, closure_date__gt=datetime.now())

def error_message(default_errors):
    field_names = []
    for field_name, field_errors in default_errors.items():
        field_names.append({"field_errors": f"{field_name.capitalize()}: {field_errors[0]}"})
    return field_names[0]['field_errors']

def MentorMarketPlaceStatus(is_certified, publish_to_marketplace):
    if is_certified and publish_to_marketplace:
        marketplace_status = "Live"
    elif not is_certified and not publish_to_marketplace:
        marketplace_status = "Pending"
    else:
        marketplace_status = "In Review"
    return marketplace_status