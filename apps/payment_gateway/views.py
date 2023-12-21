from apps.users.helper import add_user_to_company
from datetime import date, timedelta
from email.policy import HTTP
from urllib import response
from django.shortcuts import render, redirect
import braintree
from yaml import compose_all
from apps.leaderboard.views import NotificationAndPoints, send_push_notification
from apps.vonage_api.utils import journey_enrolment, payment_completion
from ravinsight.settings import BRAINTREE_MERCHANT_ID, BRAINTREE_PUBLIC_KEY, BRAINTREE_PRIVATE_KEY, BRAINTREE_PRODUCTION
from apps.content.models import Channel, UserChannel
from .models import CardDetails, Transaction, AddJourneyToCart
from apps.users.models import User, Company
from django.http import HttpResponse
from django.urls import reverse
import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.program_manager_panel.models import Subscription, SubcribedUser

if BRAINTREE_PRODUCTION:
    braintree_env = braintree.Environment.Production
else:
    braintree_env = braintree.Environment.Sandbox
braintree.Configuration.configure(braintree_env,
                                  merchant_id=BRAINTREE_MERCHANT_ID,
                                  public_key=BRAINTREE_PUBLIC_KEY,
                                  private_key=BRAINTREE_PRIVATE_KEY)


# Create your views here.


@login_required
def cart(request):
    carts = AddJourneyToCart.objects.filter(user=request.user, user_paid=False, is_added=True)
    print("cart", carts)
    total_amount = 0
    related_journeys = []
    for cart in carts:
        total_amount = total_amount + cart.journey.amount
        related_journeys.append(Channel.objects.filter(category=cart.journey.category))
    # congrates = [
    #         'https://media3.giphy.com/media/xUOrwiqZxXUiJewDrq/giphy.gif',
    #         'https://media2.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif',
    #         'https://media0.giphy.com/media/3o6Mbnll2gudglC3HG/giphy.gif',
    #         'https://media3.giphy.com/media/YP258EkezKv5RSPGRI/giphy.gif',
    #         'https://media1.giphy.com/media/puLcabEWerzmSJnPj3/giphy.gif',
    #         'https://media2.giphy.com/media/l3ZgKEvYiwSPXu1ic7/giphy.gif',
    #         'https://media2.giphy.com/media/H7YO03BHmBMWuWUkez/giphy.gif'

    #     ]
    context = {
        'carts': carts,
        'total_amount': total_amount,
        'related_journeys': related_journeys,
        # "image": random.choice(congrates),
    }
    print("carts", related_journeys)
    return render(request, 'cart.html', context)
    # return render(request, 'thankyou.html', context)


# @login_required
def add_journey_to_cart(request):
    # print("inside")
    if request.method == "POST":
        if request.user.is_authenticated:
            journey_id = request.POST['id']
            user = User.objects.get(pk=request.user.id)
            journey = Channel.objects.get(pk=journey_id)
            if AddJourneyToCart.objects.filter(journey=journey, user=user, is_added=True).exists():
                return HttpResponse("Journey Already Exist")
            else:
                try:
                    AddJourneyToCart.objects.create(user=user, journey=journey, is_added=True)
                except:
                    return HttpResponse("Something went wrong")

                return HttpResponse("Journey Added to Cart")
        else:
            response = HttpResponse("User is not authenticated")
            url = request.POST['url']
            response.set_cookie('course_detail_url', url)
            return response


@login_required
def remove_journey_from_cart(request):
    if request.method == "POST":
        journey_id = request.POST['id']
        journey = Channel.objects.get(pk=journey_id)
        try:
            cart = AddJourneyToCart.objects.filter(user=request.user, journey=journey, is_added=True)
            cart.update(is_added=False)
        except:
            return HttpResponse("Something went wrong")

        return HttpResponse("Journey Removed from Cart")


def checkout(request, pk):
    if request.user.is_authenticated:
        # print("BRAINTREE_PRODUCTION", BRAINTREE_PRODUCTION)
        clientToken = braintree.ClientToken.generate()
        journey = Channel.objects.get(pk=pk)
        if UserChannel.objects.filter(user=request.user, Channel=journey, status='Joined').exists():
            return redirect('/')
        else:
            context = {
                "clientToken": clientToken,
                "pk": pk,
                "amount": journey.amount,
                "journey": journey
            }
            return render(request, 'checkout.html', context)
    else:
        response = redirect('/login')
        response.set_cookie('course_detail_url', '/course-detail/'+str(pk))
        return response


@login_required
def checkoutSubscription(request, pk, company_id):
    if request.user.is_authenticated:
        # print("BRAINTREE_PRODUCTION", BRAINTREE_PRODUCTION)
        clientToken = braintree.ClientToken.generate()
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            raise response.Http404

        print("company", company_id)
        context = {
            "clientToken": clientToken,
            "pk": pk,
            "amount": subscription.price,
            "subscription": subscription,
            "company": company_id
        }
        return render(request, 'checkout_subscription.html', context)
    else:
        response = redirect('/login')
        # response.set_cookie('course_detail_url', '/course-detail/'+str(pk))
        return response


@login_required
def buy_cart(request):
    if request.user.is_authenticated:
        print("config", braintree_env, BRAINTREE_MERCHANT_ID, BRAINTREE_PUBLIC_KEY)
        clientToken = braintree.ClientToken.generate()
        if (AddJourneyToCart.objects.filter(user=request.user, user_paid=False, is_added=True).exists()):
            carts = AddJourneyToCart.objects.filter(user=request.user, user_paid=False, is_added=True)
            total_amount = 0
            # print("carts",carts)
            for cart in carts:
                total_amount = total_amount + cart.journey.amount
            context = {
                "clientToken": clientToken,
                "pk": 'cart',
                "amount": total_amount,
                "carts": carts
            }
            return render(request, 'checkout.html', context)
        else:
            return redirect('/')
    else:
        return redirect('/register')


@login_required
def paymentView(request):
    nonce_from_the_client = request.POST["payment_method_nonce"]
    pk = request.POST["order_pk"]
    device_data = request.POST["device_data"]

    if pk == 'cart':
        # print("true")
        carts = AddJourneyToCart.objects.filter(user=request.user, user_paid=False, is_added=True)
        total_amount = 0
        for cart in carts:
            total_amount = total_amount + cart.journey.amount

        # print(total_amount)

        result = braintree.Transaction.sale({
            "amount": total_amount,
            "payment_method_nonce": nonce_from_the_client,
            "options": {
                "submit_for_settlement": True
            },
            "device_data": device_data
        })
        # print(result)

        if result.is_success or result.transaction:

            for cart in carts:
                paid_journey = AddJourneyToCart.objects.filter(journey=cart.journey, is_added=True, user=request.user)
                paid_journey.update(user_paid=True)
                if not UserChannel.objects.filter(user=request.user, Channel=cart.journey, status='Joined').exists():
                    if cart.journey.channel_type in ["onlyCommunity", "Course"]:
                        status = "Joined"
                    else:
                        status = "Pending" if cart.journey.is_test_required else "Joined"

                    add_user_to_company(request.user, cart.journey.company)
                    UserChannel.objects.create(user=request.user, Channel=cart.journey, status=status)
                    context = {
                        "screen":"ProgramJourney",
                        "navigationPayload": { 
                            "courseId": str(cart.journey.id)
                        }
                    }
                    send_push_notification(request.user, cart.journey.title, f"You're enrolled in {cart.journey.title}", context)
                    NotificationAndPoints(request.user, "joined journey")
                    
                    if cart.journey.whatsapp_notification_required and (request.user.phone and request.user.is_whatsapp_enable):
                        journey_enrolment(request.user, cart.journey)
                    else:
                        print("phone does not exist")
                elif UserChannel.objects.filter(user=request.user, Channel=cart.journey).exists():
                    if cart.journey.channel_type in ["onlyCommunity", "Course"]:
                        status = "Joined"
                    else:
                        status = "Pending" if cart.journey.is_test_required else "Joined"

                    add_user_to_company(request.user, cart.journey.company)
                    user_channel = UserChannel.objects.filter(user=request.user, Channel=cart.journey).first()
                    user_channel.status = status
                    user_channel.save()


            expiry_date = result.transaction.credit_card_details.expiration_month + \
                "/" + result.transaction.credit_card_details.expiration_year

            cardDetails = CardDetails(method_type="Card", cardholder_name=str(result.transaction.credit_card_details.cardholder_name),
                                      last_4_card_number=result.transaction.credit_card_details.last_4, expiry_date=expiry_date)
            cardDetails.save()

            transaction = Transaction.objects.create(user=request.user, transaction_id=result.transaction.id, card_details=cardDetails, amount=result.transaction.amount, currency_code=result.transaction.currency_iso_code,
                                                     status=result.transaction.status, created_at=result.transaction.created_at, expires_at=result.transaction.authorization_expires_at, transaction_response=result)

            for cart in carts:
                transaction.journey.add(cart.journey)

            transaction.save()

            congrates = [
                'https://media3.giphy.com/media/xUOrwiqZxXUiJewDrq/giphy.gif',
                'https://media2.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif',
                'https://media0.giphy.com/media/3o6Mbnll2gudglC3HG/giphy.gif',
                'https://media3.giphy.com/media/YP258EkezKv5RSPGRI/giphy.gif',
                'https://media1.giphy.com/media/puLcabEWerzmSJnPj3/giphy.gif',
                'https://media2.giphy.com/media/l3ZgKEvYiwSPXu1ic7/giphy.gif',
                'https://media2.giphy.com/media/H7YO03BHmBMWuWUkez/giphy.gif'

            ]
            context = {
                "image": random.choice(congrates),
                "message": "Congrations! You have enrolled for the journey(s)"
            }
            return render(request, 'thankyou.html', context)

        else:
            messages.error(request, "Something went wrong, Please try again!")
            return redirect(reverse('payment_gateway:buy_cart'))

    else:

        journey = Channel.objects.get(pk=pk)
        # print(journey.amount)
        # print(pk)
        result = braintree.Transaction.sale({
            "amount": journey.amount,
            # "amount":"6.00",
            "payment_method_nonce": nonce_from_the_client,
            # "device_data": device_data_from_the_client,
            "options": {
                "submit_for_settlement": True
            },
            "device_data": device_data
            # "billing": {
            #     "postal_code": postal_code_from_the_client
            #     }
        })
        # print("result", result)
        # print(result.transaction.status)
        if not result.is_success and journey.whatsapp_notification_required:
            payment_completion(request.user, journey, result.transaction.status, pk)

        if result.is_success or result.transaction:

            if AddJourneyToCart.objects.filter(journey=journey, is_added=True, user=request.user).exists():
                print("journey", journey)
                paid_journey = AddJourneyToCart.objects.filter(journey=journey, is_added=True, user=request.user)
                paid_journey.update(user_paid=True)

            # if not UserChannel.objects.filter(user=request.user, Channel=journey, status='Joined').exists():
            #     user_channel = UserChannel(user=request.user, Channel=journey, status='Joined')
            #     user_channel.save()

            if not UserChannel.objects.filter(user=request.user, Channel=journey, status='Joined').exists():
                    if journey.channel_type in ["onlyCommunity", "Course"]:
                        status = "Joined"
                    else:
                        status = "Pending" if journey.is_test_required else "Joined"

                    add_user_to_company(request.user, journey.company)
                    UserChannel.objects.create(user=request.user, Channel=journey, status=status)
                    
                    if journey.whatsapp_notification_required and (request.user.phone and request.user.is_whatsapp_enable):
                        journey_enrolment(request.user, journey)
                    else:
                        print("phone does not exist")
            elif UserChannel.objects.filter(user=request.user, Channel=journey).exists():
                if journey.channel_type in ["onlyCommunity", "Course"]:
                    status = "Joined"
                else:
                    status = "Pending" if journey.is_test_required else "Joined"

                add_user_to_company(request.user, journey.company)
                user_channel = UserChannel.objects.filter(user=request.user, Channel=journey).first()
                user_channel.status = status
                user_channel.save()    


            expiry_date = result.transaction.credit_card_details.expiration_month + \
                "/" + result.transaction.credit_card_details.expiration_year

            cardDetails = CardDetails(method_type="Card", cardholder_name=str(result.transaction.credit_card_details.cardholder_name),
                                      last_4_card_number=result.transaction.credit_card_details.last_4, expiry_date=expiry_date)
            cardDetails.save()

            transaction = Transaction.objects.create(user=request.user, transaction_id=result.transaction.id, card_details=cardDetails, amount=result.transaction.amount, currency_code=result.transaction.currency_iso_code,
                                                     status=result.transaction.status, created_at=result.transaction.created_at, expires_at=result.transaction.authorization_expires_at, transaction_response=result)
            transaction.save()
            transaction.journey.add(journey)
            # print("transaction_id",result.transaction.credit_card_details.expiration_month)
            congrates = [
                'https://media3.giphy.com/media/xUOrwiqZxXUiJewDrq/giphy.gif',
                'https://media2.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif',
                'https://media0.giphy.com/media/3o6Mbnll2gudglC3HG/giphy.gif',
                'https://media3.giphy.com/media/YP258EkezKv5RSPGRI/giphy.gif',
                'https://media1.giphy.com/media/puLcabEWerzmSJnPj3/giphy.gif',
                'https://media2.giphy.com/media/l3ZgKEvYiwSPXu1ic7/giphy.gif',
                'https://media2.giphy.com/media/H7YO03BHmBMWuWUkez/giphy.gif'

            ]
            context = {
                "image": random.choice(congrates),
                "message": "Congrations! You have enrolled for the journey(s)"
            }
            return render(request, 'thankyou.html', context)
        else:
            messages.error(request, "Something went wrong, Please try again!")
            return redirect(f'/checkout/{pk}')


@login_required
def paymentSubscription(request):
    print("line 297", request.POST["company_pk"])
    nonce_from_the_client = request.POST["payment_method_nonce"]
    pk = request.POST["order_pk"]

    subscription = Subscription.objects.get(pk=pk)
    try:
        company = Company.objects.get(pk=request.POST["company_pk"])
    except Company.DoesNotExist:
        raise response.Http404
    print("line 302", nonce_from_the_client)
    # print(pk)
    result = braintree.Transaction.sale({
        "amount": subscription.price,
        # "amount":"6.00",
        "payment_method_nonce": nonce_from_the_client,
        # "device_data": device_data_from_the_client,
        "options": {
            "submit_for_settlement": True
        }
        # "billing": {
        #     "postal_code": postal_code_from_the_client
        #     }
    })
    print("result", result)
    # print(result.transaction.status)
    # if not result.is_success:
    #     payment_completion(request.user, journey, result.transaction.status, pk)

    if result.is_success or result.transaction:

        expiry_date = result.transaction.credit_card_details.expiration_month + \
            "/" + result.transaction.credit_card_details.expiration_year
        # company = request.user.company.all().first()
        print("company", company)
        start_date = date.today()
        user_subscription = SubcribedUser.objects.filter(
            user=request.user, is_cancel=False, company=company).order_by('updated_at').last()
        if user_subscription:
            start_date = user_subscription.end_date + timedelta(days=1)
        subcribeUser = SubcribedUser.objects.create(
            user=request.user, subscription=subscription, company=company, is_subscribed=True, start_date=start_date)
        subcribeUser.subscription_end_time(start_date, subscription.duration, subscription.duration_type)
        cardDetails = CardDetails(method_type="Card", cardholder_name=str(result.transaction.credit_card_details.cardholder_name),
                                  last_4_card_number=result.transaction.credit_card_details.last_4, expiry_date=expiry_date)
        cardDetails.save()

        Transaction.objects.create(user=request.user, company=company, subscription=subscription, transaction_id=result.transaction.id, card_details=cardDetails, amount=result.transaction.amount, currency_code=result.transaction.currency_iso_code,
                                   status=result.transaction.status, created_at=result.transaction.created_at, expires_at=result.transaction.authorization_expires_at, transaction_response=result)
        # print("transaction_id",result.transaction.credit_card_details.expiration_month)
        congrates = [
            'https://media3.giphy.com/media/xUOrwiqZxXUiJewDrq/giphy.gif',
            'https://media2.giphy.com/media/xT0xezQGU5xCDJuCPe/giphy.gif',
            'https://media0.giphy.com/media/3o6Mbnll2gudglC3HG/giphy.gif',
            'https://media3.giphy.com/media/YP258EkezKv5RSPGRI/giphy.gif',
            'https://media1.giphy.com/media/puLcabEWerzmSJnPj3/giphy.gif',
            'https://media2.giphy.com/media/l3ZgKEvYiwSPXu1ic7/giphy.gif',
            'https://media2.giphy.com/media/H7YO03BHmBMWuWUkez/giphy.gif'

        ]
        context = {
            "image": random.choice(congrates),
            "message": "Congrations! You have successfully subscribed to the plan."
        }
        return render(request, 'thankyou.html', context)
    else:
        messages.error(request, "Something went wrong, Please try again!")
        return redirect(f'/checkout/subscription/{pk}')


@login_required
def show_payment(request):
    journeys = Channel.objects.all()
    transactions = Transaction.objects.filter(journey__in=journeys)
    context = {
        "transactions": transactions,
    }
    return render(request, 'show_payment.html', context)

@login_required
def company_subscription_payment(request):
    companys = Company.objects.all()
    transactions = Transaction.objects.filter(company__in=companys)
    context = {
        "transactions": transactions,
    }
    return render(request, 'company-subscription.html', context)