import imp
from django.db.models.query import QuerySet
from django.utils import timezone
from swapper import load_model
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.dispatch import Signal
import uuid
from apps.users.models import User
from apps.utils.models import Timestamps, ModelActiveDelete
from ravinsight.constants import rsvp_choices, meet_type

# Create your models here.

class AtPaceNotification(Timestamps):
    category_type = (
        ("Plateform", "Plateform"),
        ("AtPace_Community", "AtPace_Community"),
    )
    type = (
        ("Post", "Post"),
        ("PostLike", "PostLike"),
        ("CommentLike", "CommentLike"),
        ("Comment", "Comment"),
        ("Replies", "Replies"),
        ("SignUp", "SignUp"),
        ("Mentions", "Mentions"),
        ("Direct", "Direct"),
        ("Weekly_Digest", "Weekly_Digest"),
        ("Report", "Report"),
        ("Archive", "Archive"),
        ("Share", "Share"),
    )
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, related_name='notifications_to', on_delete=models.CASCADE)
    unread = models.BooleanField(default=True, blank=False)
    by_user_obj = models.ForeignKey(ContentType, related_name='notify_by_user_id', on_delete=models.CASCADE)
    by_user_id = models.CharField(max_length=255)
    action_id = models.JSONField(null=True)
    by_user = GenericForeignKey('by_user_obj', 'by_user_id')
    verb = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=category_type, default="AtPace_Community")
    notification_types = models.CharField(max_length=50, choices=type, default="Post")
    description = models.TextField(blank=True, null=True)
    is_delete = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        ctx = {
            'actor': self.by_user,
            'verb': self.verb,
            'timesince': self.timesince()
        }
        return u'%(actor)s %(verb)s %(timesince)s ago' % ctx

    def timesince(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """
        from django.utils.timesince import timesince as timesince_
        return timesince_(self.created_at, now)

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save()


def notify_handler(verb, **kwargs):
    """
    Handler function to create Notification instance upon action signal call.
    """
    # Pull the options out of kwargs
    kwargs.pop('signal', None)
    recipient = kwargs.pop('to_user')
    actor = kwargs.pop('sender')
    description = kwargs.pop('description', None)
    created_at = kwargs.pop('timestamp', timezone.now())
    notification_types = kwargs.pop('notification_types')
    category = kwargs.pop('category')
    action_id = kwargs.pop('action_id')
    Notification = load_model('push_notification','AtPaceNotification')

    if isinstance(recipient, (QuerySet, list)):
        recipients = recipient
    else:
        recipients = [recipient]

    new_notifications = []

    for recipient in recipients:
        newnotify = Notification(
            to_user=recipient,
            by_user_obj=ContentType.objects.get_for_model(actor),
            by_user_id=actor.pk,
            verb=str(verb),
            action_id=action_id,
            description=description,
            notification_types=notification_types,
            category=category,
            created_at=created_at,
        )

        newnotify.save()
        new_notifications.append(newnotify)

    return new_notifications


# notifye = Signal(providing_args=[
#     'to_user', 'by_user', 'verb', 'description', 'timestamp', 
#     'category', 'notification_types', 'action_id'
# ])

notifye = Signal()

# connect the signal
notifye.connect(notify_handler, dispatch_uid='AtPaceNotification')


class MeetRSVPData(Timestamps, ModelActiveDelete):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meet_id = models.CharField(max_length=50)
    meet_type = models.CharField(max_length=50, choices=meet_type)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="RSVP_by")
    response = models.CharField(max_length=10, choices=rsvp_choices)
    notification_id = models.CharField(max_length=100)
