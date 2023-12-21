import random
import vonage
from django.utils.html import strip_tags
from apps.users.templatetags.tags import get_chat_room
from apps.utils.models import UrlShortner
from .models import VonageApiHistory, VonageWhatsappReport
from apps.atpace_community.models import Post, Comment
import json
from ravinsight.web_constant import BASE_URL, VONAGE_NUMBER, COMMUNITY_URL, VONAGE_URL, VONAGE_NAMESPACE, VONAGE_KEY, VONAGE_SECRET
from ravinsight.settings.base import BASE_DIR
import requests
import datetime
import phonenumbers
from nexmo_jwt import JWTokenGenerator

def url_shortner(long_url, domain):
    if url := UrlShortner.objects.filter(long_url=long_url).first():
        return f"{domain}/re/{url.short_url}"

    s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    short_url = ("".join(random.sample(s, 6)))
    UrlShortner.objects.create(long_url=long_url, short_url=short_url)

    return f"{domain}/re/{short_url}"

def status_update(data):
    if status_report := VonageWhatsappReport.objects.filter(message_id=data['message_uuid']):
        if data['status'] == "rejected":
            status_report.update(message_status=data['status'])
        elif data['status'] == "submitted":
            status_report.update(is_sent=True, message_status=data['status'])
        elif data['status'] == "read":
            status_report.update(is_seen=True)
        elif data['status'] == "delivered":
            status_report.update(is_delivered=True)

def generate_vonage_token():
    gen: JWTokenGenerator = JWTokenGenerator('a2eff165-1aa1-4cf3-83fd-26b89165a77b',f'{BASE_DIR}/static/cred/private.key')
    token: bytes = gen.generate_token()
    print(type(token))
    if isinstance(token, bytes):
        return str(token).replace("b'","").replace("'","")
#         return token.decode("utf-8")
    return token

def create_vonage_api_record(from_user, to_user, message_type, user, post, message_id, message):
    print("message_id", message_id)
    vonage = VonageApiHistory.objects.create(message_type=message_type, user=user, post_id=post.id,
                                    message_id=message_id, message_from=from_user, message_to=to_user, message=message)
    print("vonage", vonage)
    return True


def update_message_status(data):
    message_id = data['message_uuid']
    status = data['status']
    VonageApiHistory.objects.filter(message_id=message_id).update(message_status=status)
    return True


def create_message_reply(data):
    if parent_message_id := data['context']['message_uuid'] if "context" in data else '':
        text = data["text"] if "text" in data else data['button']['payload']
        print("text ",text)
        vonage_data = VonageApiHistory.objects.filter(message_id=parent_message_id)
        to_user = data['to']
        from_user = data['from']
        if vonage_data.count() > 0:
            vonage_data = vonage_data.first()
            if text in ["Open App for options", "Open App"]:
                create_vonage_post_comment(vonage_data.post_id, vonage_data.user, text)
            else:
                send_message(from_user, to_user, text)
        else:
            send_message(from_user, to_user)
        return True
    return False


def create_vonage_post_comment(post_id, user, text):
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return False
    comment = Comment.objects.create(Body=text, post=post, created_by=user, parent_id=None)
    comment_recorded_confirmation(user, text)
    return True


def user_phone_with_country_code(user):
    mobile = str(user.phone)
    try:
        number = phonenumbers.parse(mobile, None).national_number
        country_code = phonenumbers.parse(mobile, None).country_code
    except Exception:
        return False
    return f'{country_code}{number}'


def send_message(from_user, to_user, message=None):
    if message in ["Open App for options", "Open App"]:
        message = "If you have any query. Please Connect with Support team Info@growatpace.com"
    else:
        message = f"Click on link below to Open App\n\n {url_shortner(f'{BASE_URL}/api/atpace/app/', BASE_URL)}"

    message_type = "text"
    payload = json.dumps({
        "from": to_user,
        "to": from_user,
        "message_type": message_type,
        "text": message,
        "channel": "whatsapp"
    })
    token = generate_vonage_token()
    # create_vonage_api_record(from_user = from_user, to_user = to_user, message_type=message_type, user = user, post= post)
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {token}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    return True


def send_chat_info(user, message):
    to_user = user_phone_with_country_code(user)
    if not to_user:
        return "Phone Number not valid"
    message_type = "text"
    from_user = VONAGE_NUMBER
    message_type = "text"
    payload = json.dumps({
        "from": from_user,
        "to": to_user,
        "message_type": message_type,
        "text": message,
        "channel": "whatsapp"
    })

    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)

    return True


def appointment_cancel_reminder(to, user, mentor, session):
    room = get_chat_room(user, mentor)
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(to)
    if not to_number:
        return "Phone Number not valid"
    learner_name = "Prashant Kumar"
    mentor_name = "Mentor"
    date_time = "Jan 20"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",
        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "appointment_cancelled",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{mentor.first_name} {mentor.last_name}"
                            },
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            },
                            {
                                "type": "text",
                                "text": str(session)
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/Book-mentor-slots/", BASE_URL) 
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/chat/{room}/", BASE_URL)
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)

    return True


def appointment_update_reminder(to, user, mentor, session, meet_url):
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(to)
    if not to_number:
        return "Phone Number not valid"
    learner_name = "Prashant Kumar"
    mentor_name = "Mentor"
    date_time = "Jan 20"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",
        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "atpace_appt_reminderv2",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{mentor.first_name} {mentor.last_name}"
                            },
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            },
                            {
                                "type": "text",
                                "text": str(session)
                            },
                            {
                                "type": "text",
                                "text": meet_url
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/user-calendar/", BASE_URL)
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type" : "url",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": "re"+url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL).split("re")[1]
                            }
                        ]
                    }
                ]
            }
        }
    })

    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)

    return True


def community_update(user, post):
    from_number = VONAGE_NUMBER
    body = strip_tags(post.Body[:100])

    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",
        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "community_post_update_v3",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                        {
                            "type": "header",
                            "parameters": [{
                                "type": "image",
                                "image": {
                                    "link": post.cover_image.url if post.cover_image else "https://growatpace.com/static/website/img/logo.png"
                                }
                            }]
                        },
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": f"{post.created_by.first_name} {post.created_by.last_name}"
                                },
                                {
                                    "type": "text",
                                    "text": post.title
                                },
                                {
                                    "type": "text",
                                    "text": str(body)
                                }
                            ]
                        },
                        {
                            "type": "button",
                            "sub_type": "url",
                            "index": 0,
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": f"post-details/{post.id}"
                                }
                            ]
                        }
                ]
            }
        }
    })
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    message_id = response.json()['message_uuid']
    create_vonage_api_record(str(from_number), to_number, "custom", user, post, message_id, f"{post.title} Created")

    return True


def enroll_lite(user, journey, user_type=None):
    from_number = VONAGE_NUMBER
    if user_type is None:
        user_type = ",".join(str(type.type) for type in user.userType.all())
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "enroll_lite",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": journey.title
                            },
                            {
                                "type": "text",
                                "text":  user_type
                            },
                            {
                                "type": "text",
                                "text": "https://forum.growatpace.com/"
                            },
                            {
                                "type": "text",
                                "text": "info@growatpace.com"
                            },
                            
                        ]
                    }
                ]
            }
        }
    })

    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
               'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)

    return True


def journey_enrolment(user, journey):
    valid_till = datetime.date.today()+datetime.timedelta(days=journey.enroll_validity)
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "program_enrolv3_dynamic",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": journey.title
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/course-detail/{journey.id}", BASE_URL)
                            },
                            {
                                "type": "text",
                                "text": str(valid_till)
                            }
                            ,
                            {
                                "type": "text",
                                "text": "https://growatpace.com/program"
                            }
                            ,
                            {
                                "type": "text",
                                "text": "https://forum.growatpace.com/"
                            }
                            ,
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL)
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type" : "url",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": "re"+url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL).split("re")[1]
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def live_stream_event(user, title, speaker, session):
    from_number = VONAGE_NUMBER

    # to_number = 918319035085    
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "live_stream_event_added",
                "language": {
                    "policy": "deterministic",
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": title
                            },
                            {
                                "type": "text",
                                "text": f"{speaker.first_name} {speaker.last_name}"
                            },
                            {
                                "type": "text",
                                "text": str(session)
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def payment_completion(user, journey, status, channel_id):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "payment_completion",
                "language": {
                    "policy": "deterministic",
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": journey.title
                            },
                            {
                                "type": "text",
                                "text": status
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type" : "url",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": "re"+url_shortner(f"{BASE_URL}/checkout/{channel_id}", BASE_URL).split("re")[1]
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def program_team_broadcast(user, announcement, manager):
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    print(f"to_number: {to_number}")
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "program_team_broadcast",
                "language": {
                    "policy": "deterministic",
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{manager.first_name} {manager.last_name}"
                            },
                            {
                                "type": "text",
                                "text": announcement.topic
                            },
                            {
                                "type": "text",
                                "text": announcement.summary
                            }
                        ]
                    }
                ]
            }
        }
    })
    print("payload",payload)
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    message_id = response.json().get('message_uuid')
    VonageWhatsappReport.objects.create(id=message_id, message_id=message_id, announcement=announcement, from_user=str(VONAGE_NUMBER), user=user, message_type="Program Team Broadcast")
    print("response.text",response.text)

    return response

def appointment_reschedule(user, mentor, session):
    
    from_number = VONAGE_NUMBER
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    learner_name = "Prashant Kumar"
    mentor_name = "Mentor"
    date_time = "Jan 20"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",
        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "atpace_appt_reschedule",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{mentor.first_name} {mentor.last_name}"
                            },
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            },
                            {
                                "type": "text",
                                "text": str(session)
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/user-calendar/", BASE_URL)
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/user-calendar/", BASE_URL)
                            },
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/user-calendar/", BASE_URL)
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type" : "url",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": "re"+url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL).split("re")[1]
                            }
                        ]
                    }
                ]
            }
        }
    })

    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def general_message(user):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "general_message_v2",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            },
                            {
                                "type": "text",
                                "text": "topic"
                            },
                            {
                                "type": "text",
                                "text": "summary"
                            },
                            {
                                "type": "text",
                                "text": "program_team_email"
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def comment_recorded_confirmation(user, comment):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "comment_recorded_confirmation",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": comment.Body
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def user_credentail_info(user, password):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "user_credentail_infov2",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": user.email
                            },
                            {
                                "type": "text",
                                "text": password
                            },
                            {
                                "type": "text",
                                "text": "https://growatpace.com/program"
                            },
                            {
                                "type": "text",
                                "text": "https://forum.growatpace.com"
                            }
                            ,
                            {
                                "type": "text",
                                "text":  url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL)
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def whatsapp_otp_login(user, otp):
    from_number = VONAGE_NUMBER
    
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",
        "custom": {
            "type": "template",
            "template": {
                "namespace": "e45f8724_53d6_423b_bbf0_df214cb4f9d5",
                "name": "otp_new",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
            {
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": str(otp)
                    }
                ]
            },
            {
                "type": "button",
                "sub_type": "url",
                "index": 0,
                "parameters": [
                    {
                        "type": "text",
                        "text": str(otp)
                    }
                ]
            }
        ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def password_reset(user, link):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "password_reset",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            },
                            {
                                "type": "text",
                                "text": link
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def first_time_registration(user, password):
    from_number = VONAGE_NUMBER
    
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "firsttime_registration",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": user.email
                            },
                            {
                                "type": "text",
                                "text": password
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def reminder_to_journnal_scheduler(user, journal_id):
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "reminder_to_journal",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": BASE_URL+f"/learning-journal-post/{user.id}/{journal_id}",
                            }
                        ]
                    },
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True


def program_team_weekly_scheduler(user, date, journey, microskill_perc, journal_perc, no_acivity_pairs):
    from_number = VONAGE_NUMBER

    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "program_team_weekly",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": date
                            },
                            {
                                "type": "text",
                                "text": journey
                            },
                            {
                                "type": "text",
                                "text": microskill_perc
                            },
                            {
                                "type": "text",
                                "text": journal_perc
                            },
                            {
                                "type": "text",
                                "text": no_acivity_pairs
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": 0,
                        "parameters": [
                            {
                                "type": "text",
                                "text": BASE_URL
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def lets_start_work_checkjourney(user):
    from_number = VONAGE_NUMBER
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "lets_start_work_checkjourney",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "button",
                        "sub_type" : "quick_reply",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL)
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def lets_start_work_journal(user):
    from_number = VONAGE_NUMBER
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "learn_start_work_journal",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{user.first_name} {user.last_name}"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type" : "quick_reply",
                        "index": 0, 
                        "parameters": [
                            {
                                "type": "text",
                                "text": url_shortner(f"{BASE_URL}/api/atpace/app/", BASE_URL)
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True

def book_a_call_one_mentor(user, mentor_name, day_time):
    from_number = VONAGE_NUMBER
    # to_number = 918319035085
    to_number = user_phone_with_country_code(user)
    if not to_number:
        return "Phone Number not valid"
    payload = json.dumps({
        "from": from_number,
        "to": to_number,
        "channel": "whatsapp",
        "message_type": "custom",

        "custom": {
            "type": "template",
            "template": {
                "namespace": VONAGE_NAMESPACE,
                "name": "book_a_call_one_mentor",
                "language": {
                    "policy": "deterministic",
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": mentor_name
                            },
                            {
                                "type": "text",
                                "text": day_time
                            }
                        ]
                    }
                ]
            }
        }
    })
    
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f"Bearer {generate_vonage_token()}"}

    response = requests.request("POST", VONAGE_URL, headers=headers, data=payload)
    

    return True