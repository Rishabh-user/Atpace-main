from apps.users.models import *
from apps.mentor.models import *
from apps.content.models import *
import boto3
import json

# AWS creds
ACCESS_ID = "AKIA6MXK4RXL2RHJFKLG"
ACCESS_KEY = "eX9iKe2yCcJkTnUVb9SwKqAETtdOXF0CsU6tp7Ew"

# Initialize AWS SageMaker clients
client = boto3.client("sagemaker-runtime", aws_access_key_id=ACCESS_ID,       
        aws_secret_access_key= ACCESS_KEY, region_name='ap-south-1')


def invoke_endpoint(client, data):
    ENDPOINT_NAME = "huggingface-summarization12-4-svl"
    response = client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Accept="application/json",
        Body=json.dumps({"inputs": data}),
    )
    result = json.loads(response["Body"].read().decode()) if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200 else None
    return result


def process_data(profile:dict, profession:str):
    if profession.lower() == 'mentee' or profession.lower() == 'mentor':
        if profile.get('Expertize'): profile["responses"].append(f"I have Expertize in {profile['Expertize']}.")

        if profile.get('Interested Topic'): profile["responses"].append(f"I have Interest in {profile['Interested Topic']}.")

        if profile.get('Industry'): profile["responses"].append(f"The industry in which I work in is {profile['Industry']}.")

        if profile.get('Organization'): profile["responses"].append(f"I work in an organisation named {profile['Organization']}.")

        if profile.get('Position'): profile["responses"].append(f"My position at work is {profile['Position']}.")

        if profile.get('Profile Heading'): profile["responses"].append(f"Profile Heading: {profile['Profile Heading']}.")

        if profile.get('Upscaling Reason'): profile["responses"].append(f"I am upscaling myself because {profile['Upscaling Reason']}.")

        if profile.get('Favourite Way to Learn'): profile["responses"].append(f"My favorite way to learn is {profile['Favourite Way to Learn']}.")

        if profile.get('About Us'): profile["responses"].append(f"About me: {profile['About Us']}.")

        if profile.get('responses'):
            for response in profile.get('responses'): profile["responses"].append(f"About me: {profile['About Us']}.")

        detail = '.'.join(profile.get('responses'))
        summary = invoke_endpoint(client, detail)
        if summary[0].get('summary_text'):
            return summary[0]['summary_text']
    return None


def mentee_summary():
    mentee_obj = UserChannel.objects.filter(Channel__is_active = True, user__is_active=True)
    for user in mentee_obj:
        user_profile_assest = UserProfileAssest.objects.filter(user=user.user)
        mentee_response = [ assest.response for assest in user_profile_assest ]
        profile = {
            "ID": str(user.user.id),
            "Name": user.user.get_full_name(),
            "Email": user.user.email,
            "Profession": "Mentee",
            "About Us": user.user.about_us,
            "Position": user.user.position,
            "Profile Heading": user.user.profile_heading,
            "Expertize": ", ".join(str(expertize.name) for expertize in user.user.expertize.all()),
            "Industry": ", ".join(str(industry.name) for industry in user.user.industry.all()),
            "Favourite Way to Learn": user.user.favourite_way_to_learn.replace(",", ", "),
            "Interested Topic": user.user.interested_topic.replace(",", ", "),
            "Upscaling Reason": user.user.upscaling_reason.replace(",", ", "),
            "Organization": user.user.organization,
            "responses": mentee_response
        }
        
        result = process_data(profile, "mentee")
        if result:
            learner = User.objects.get(userType__type="Learner", email=user.user.email)
            MenteeSummary.objects.create(mentee=learner, summary=result, journey=user.Channel)
            print(f"Object was created for {user.user.email}")
        else: print(f"Record was not created for {user.user.email}")


def mentor_summary():
    mentor_obj = PoolMentor.objects.filter(pool__journey__is_active=True, is_active=True, mentor__is_active=True)
    for mentor in mentor_obj:
        mentor_response = []
        mentor_profile_assest = UserProfileAssest.objects.filter(user=mentor.mentor)
        mentor_response = [ assest.response for assest in mentor_profile_assest ]
        profile = {
            "ID": str(mentor.mentor.id),
            "Name": mentor.mentor.get_full_name(),
            "Email": mentor.mentor.email,
            "Profession": "Mentor",
            "About Us": mentor.mentor.about_us,
            "Position": mentor.mentor.position,
            "Profile Heading": mentor.mentor.profile_heading,
            "Expertize": ", ".join(str(expertize.name) for expertize in mentor.mentor.expertize.all()),
            "Industry": ", ".join(str(industry.name) for industry in mentor.mentor.industry.all()),
            "Favourite Way to Learn": mentor.mentor.favourite_way_to_learn.replace(",", ", "),
            "Interested Topic": mentor.mentor.interested_topic.replace(",", ", "),
            "Upscaling Reason": mentor.mentor.upscaling_reason.replace(",", ", "),
            "Organization": mentor.mentor.organization,
            "responses": mentor_response
        }
    
        result = process_data(profile, "mentee")
        if result:
            mentor = User.objects.get(userType__type="Mentor", email=mentor.user.email)
            MenteeSummary.objects.create(mentee=mentor, summary=result, journey=mentor.Channel)
            print(f"Object was created for {mentor.user.email}")
        else: print(f"Record was not created for {mentor.user.email}")

