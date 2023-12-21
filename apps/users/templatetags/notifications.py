from notifications.models import Notification
from django import template
register = template.Library()

@register.filter(name='notification_count')
def notification_count(user):
    return Notification.objects.filter(recipient=user).count()

@register.filter(name='notification_list')
def notification_list(user):
    notification__list = Notification.objects.filter(recipient=user, unread=True).order_by('-timestamp')
    # notification__list.update(unread=False)
    return notification__list[:8]