# chat/urls.py
from django.urls import path
from .views import add_journey_to_cart, remove_journey_from_cart, checkoutSubscription, paymentSubscription, company_subscription_payment

from . import views

app_name = 'payment_gateway'
urlpatterns = [
    path('<uuid:pk>', views.checkout, name='checkout'),
    path('payment', views.paymentView, name='payment'),
    path('subscription-payment', views.paymentSubscription, name='payment-subscription'),
    path('add-journey-to-cart/', views.add_journey_to_cart, name="add_journey_to_cart"),
    path('remove-journey-from-cart/', views.remove_journey_from_cart, name="remove_journey_from_cart"),
    path('cart', views.cart, name='cart'),
    path('buy', views.buy_cart, name='buy_cart'),
    path('show-payment', views.show_payment, name='show-payment'),
    path('subscription/<uuid:pk>/<uuid:company_id>', views.checkoutSubscription, name='checkout-subscription'),
    path('company-subscription/', company_subscription_payment, name="company_subscription")
]
