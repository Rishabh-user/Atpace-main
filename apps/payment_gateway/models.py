from apps.program_manager_panel.models import Subscription
from django.db import models
import uuid
from apps.users.models import Coupon, User, Company
from apps.content.models import Channel

# Create your models here.

class CardDetails(models.Model):
    choices = (
        ("Card" , "Card"),
        ("GooglePay" , "GooglePay"),
        ("Paypal" , "Paypal"),
        ("ApplePay" , "ApplePay"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    method_type = models.CharField(choices=choices, max_length=255, default="Card")
    cardholder_name = models.CharField(max_length=255, blank=True)
    last_4_card_number = models.CharField(max_length=255, blank=True)
    expiry_date = models.CharField(max_length=255, blank=True)
    address_line_1 = models.TextField(blank=True)
    address_line_2 = models.TextField(blank=True)
    country = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    post_code = models.IntegerField(null=True)
    state = models.CharField(max_length=255, blank=True)




class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ManyToManyField(Channel)
    transaction_id = models.CharField(max_length=255)
    card_details = models.ForeignKey(CardDetails, on_delete = models.CASCADE)
    amount = models.IntegerField()
    currency_code = models.CharField(max_length=255)
    discount = models.IntegerField(default=0)
    # coupon = models.ForeignKey(Coupon, on_delete = models.CASCADE)
    status = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now=False, auto_now_add=False)
    expires_at = models.DateTimeField(null=True, blank=True, auto_now=False, auto_now_add=False)
    transaction_response = models.TextField()


class AddJourneyToCart(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    journey = models.ForeignKey(Channel, on_delete = models.CASCADE)
    total_amount = models.IntegerField(default=0)
    user_paid = models.BooleanField(default=False)
    is_added = models.BooleanField(default=True)

    # def __str__(self):
    #     return self.journey







