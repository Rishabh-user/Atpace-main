import requests
from django.shortcuts import render
from apps.community.models import CicleDataDump, CommunityPost, CommunityPostComment
from googleapiclient.discovery import build
from google.oauth2 import service_account
from apps.webapp.models import DeviceDetails
from apps.content.models import MentoringJourney, Channel, Content


def public_Post_Comment(post_id, body, space_id, community_id, user):
    space_id = space_id
    community_id = community_id
    post_id = post_id
    # group_id = space_group_id
    url = "https://app.circle.so/api/v1/comments/?community_id=" + \
        str(community_id)+"&space_id="+str(space_id)+"&post_id=" + \
        str(post_id)+"&body="+str(body)+"&user_email="+str(user.email)

    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.post(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    if data['success']:
        data = data['comment']
        id = data['id']

        space_id = data['space_id']
        community_id = data['community_id']
        body = data['body']['body']
        post_id = data['post_id']
    CicleDataDump.objects.create(data=data, type="community_post_comment")

    try:
        community_post = CommunityPost.objects.get(post_id=post_id)
    except CommunityPost.DoesNotExist:
        community_post = None
    CommunityPostComment.objects.create(comment_id=id, community_post=community_post,  post_id=post_id,
                                        space_id=space_id, community_id=community_id, body=body)
    return True


def space_groups(community_id):
    community_id=community_id
    
    url = "https://app.circle.so/api/v1/space_groups?"+"community_id="+str(community_id)
    
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    return data


def spaces(community_id):
    community_id = community_id
    
    # url = "https://app.circle.so/api/v1/spaces/{}?community_id={}".format(id, community_id)
    url = "https://app.circle.so/api/v1/spaces?community_id={}&sort=active&per_page=100&page=1".format(community_id)
    headers = {
        'Authorization': 'Token TeWPTHJrtyjdXbH8qUva4G4g'
    }
    response_body = requests.get(
        url=url,
        headers=headers,
    )
    data = response_body.json()
    return data


def add_user_to_sheets(name, email):
    user_list= []
    user_list.append([name,email])
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'static/cred/atpaceKeys.json'

    creds = None
    creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # The ID of spreadsheet.
    SAMPLE_SPREADSHEET_ID = '18mgR7eYNJEFRwGSNGmJPYo55m6JDosCArvYNBiHoZ4Q'

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    request = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                            range="Sheet1!A2", valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body={"values":user_list}).execute()
    # result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
    #                             range="day1!A{i}:B{j}").execute()
    # i+=1
    # j+=1
    # values = result.get('values', [])
    # print(values)
    return True

def user_device(user_agent, user):
    if user_agent.is_mobile:
        device_type = "Mobile"
    elif user_agent.is_tablet:
        device_type = "Tablet"
    elif user_agent.is_pc:
        device_type = "Pc"
    os_type = user_agent.os.family
    os_version = user_agent.os.version_string
    device = user_agent.device.family
    DeviceDetails.objects.create(user = user, os_type=os_type, 
                    device_type=device_type, os_version=os_version, device=device)
    return True


def journey_content_list(journey):
    if journey.channel_type == "MentoringJourney":
        content = MentoringJourney.objects.filter(journey=journey, is_delete=False)
        # print("content")
    elif journey.channel_type == "SkillDevelopment":
        content = Channel.objects.filter(parent_id=journey)
        # print("content")
    else:
        content = Content.objects.filter(Channel=journey)
    return content

def renderpartners(request):
    print("rendering the things")
    return render(request, "website/parnters.html")