import math
import re
from collections import Counter
import boto3
import json
import concurrent.futures

# AWS creds
ACCESS_ID = "AKIA6MXK4RXL2RHJFKLG"
ACCESS_KEY = "eX9iKe2yCcJkTnUVb9SwKqAETtdOXF0CsU6tp7Ew"

# Initialize AWS SageMaker clients
client = boto3.client("sagemaker-runtime", aws_access_key_id=ACCESS_ID,
         aws_secret_access_key= ACCESS_KEY, region_name='ap-south-1')

WORD = re.compile(r"\w+")

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    return float(numerator) / denominator if denominator else 0.0

def text_to_vector(text:str):
    words = WORD.findall(text)
    return Counter(words)

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

def process_data(profile_details:list, profession:str):
    for profile in profile_details:
        if profession.lower() == 'mentee':
            if profile.get('Expertize'):
                profile["responses"].append(f"I have Expertize in {profile['Expertize']}.")
            if profile.get('Interested Topic'):
                profile["responses"].append(f"I have Interest in {profile['Interested Topic']}.")

        detail = '.'.join(profile.get('responses'))
        if not profile.get('Summary'):
            summary = invoke_endpoint(client, detail)
            profile['Summary'] = summary[0]['summary_text']

def process_mentee(mentee, mentors):
    process_data(profile_details=[mentee], profession='mentee')

def process_mentor(mentor, mentees):
    process_data(profile_details=[mentor], profession='mentor')

def best_matches(mentees:list, mentors:list, num_top_mentors:int=3):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_mentee = {executor.submit(process_mentee, mentee, mentors): mentee for mentee in mentees}
        future_to_mentor = {executor.submit(process_mentor, mentor, mentees): mentor for mentor in mentors}

        concurrent.futures.wait(future_to_mentee, timeout=None)
        concurrent.futures.wait(future_to_mentor, timeout=None)

    response = [] 

    mentee = mentees[0]

    # Create a list to store the top mentors and their similarity scores
    top_mentors = []

    for mentor in mentors:
        if mentor['mentor__id'] != mentee['mentee__id']:
            text1 = mentee.get('summary')
            text2 = mentor.get('summary')
            vector1 = text_to_vector(text=text1)
            vector2 = text_to_vector(text=text2)

            cosine = get_cosine(vector1, vector2)
            mentor['CosineSimilarity'] = cosine

            # Add mentor to the top_mentors list if it's one of the top five mentors based on cosine similarity
            if len(top_mentors) < num_top_mentors:
                top_mentors.append(mentor)
            else:
                min_cosine_mentor = min(top_mentors, key=lambda x: x['CosineSimilarity'])
                if cosine > min_cosine_mentor['CosineSimilarity']:
                    top_mentors.remove(min_cosine_mentor)
                    top_mentors.append(mentor)

    # Sort the top_mentors list based on similarity in descending order
    top_mentors.sort(key=lambda x: x['CosineSimilarity'], reverse=True)

    for i, mentor in enumerate(top_mentors, start=1):
        score = round(mentor['CosineSimilarity'], 3) * math.e * 100 if mentor['CosineSimilarity'] * math.e < 1 else 98.9
        response.append(json.dumps({'ID':str(mentor['mentor__id']), 'Name':mentor['mentor__first_name'], 'Score':score}))

    return response