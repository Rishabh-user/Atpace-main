# from django.db.models import signals
# from django.dispatch import receiver
# from apps.users.models import User
  
# from apps.users.models import *
# from apps.mentor.models import *
# from apps.content.models import *
# import boto3
# from django.db.models import Q
# from apps.users.utils import invoke_endpoint, process_data
# from ravinsight.settings.base import SUMMARY_ACCESS_ID, SUMMARY_ACCESS_KEY

# from apps.users.models import *
# from apps.mentor.models import *
# from apps.content.models import *

# # Initialize AWS SageMaker clients
# client = boto3.client("sagemaker-runtime", aws_access_key_id=SUMMARY_ACCESS_ID,       
#         aws_secret_access_key= SUMMARY_ACCESS_KEY, region_name='ap-south-1')

# def create_profile(user, user_type, journey=None):
#    mentor_response = []   
#    if journey:
#       mentor_profile_assest = UserProfileAssest.objects.filter(~Q(assess_question__journey=journey.id),  user=user)
#       mentor_response = [ assest.response for assest in mentor_profile_assest ]

#    if user_type == "Mentor":
#       profile = {
#                   "Name": user.get_full_name(),
#                   "Email": user.email,
#                   "Profession": "Mentor",
#                   "About Us": user.about_us,
#                   "Position": user.position,
#                   "Profile Heading": user.profile_heading,
#                   "Expertize": ", ".join(str(expertize.name) for expertize in user.expertize.all()),
#                   "Industry": ", ".join(str(industry.name) for industry in user.industry.all()),
#                   "Favourite Way to Learn": user.favourite_way_to_learn.replace(",", ", "),
#                   "Interested Topic": user.interested_topic.replace(",", ", "),
#                   "Upscaling Reason": user.upscaling_reason.replace(",", ", "),
#                   "Organization": user.organization,
#                   "responses": mentor_response
#                }
#    elif user_type == "Learner":
#       profile = {
#                   "Name": user.get_full_name(),
#                   "Email": user.email,
#                   "Profession": "Learner",
#                   "About Us": user.about_us,
#                   "Position": user.position,
#                   "Profile Heading": user.profile_heading,
#                   "Expertize": ", ".join(str(expertize.name) for expertize in user.expertize.all()),
#                   "Industry": ", ".join(str(industry.name) for industry in user.industry.all()),
#                   "Favourite Way to Learn": user.favourite_way_to_learn.replace(",", ", "),
#                   "Interested Topic": user.interested_topic.replace(",", ", "),
#                   "Upscaling Reason": user.upscaling_reason.replace(",", ", "),
#                   "Organization": user.organization,
#                   "responses": mentor_response
#                }
   
#    return profile

# def get_summary(profile, profession):
#    summary = process_data(profile, profession, client)
#    return summary

# @receiver(signals.post_save, sender=User)
# def update_summary(sender, instance, **kwargs):
#    user = User.objects.get(email=instance.email)
#    user_types = [t.type for t in user.userType.all()]
#    if "Mentor" in user_types:
#       profile = create_profile(user, "Mentor")
#       summary = get_summary(profile, "Mentor")
#       mentor_summary = MentorSummary.objects.filter(mentor=user)
#       if mentor_summary:
#          mentor_summary.update(summary=summary)
#          print("User details updated")
#       else:
#          pool_mentor = PoolMentor.objects.get(mentor=user)
#          if not pool_mentor:
#             pool_mentor = UserChannel.objects.get(user=user)
#          MentorSummary.objects.create(mentor=user, journey=pool_mentor.Channel)
#       print("Details updated")

#    # if kwargs['created']:
#    #    if "Mentor" in user_types:
#    #       profile = create_profile(user, "Mentor")
#    #       summary = get_summary(profile, "Mentor")
#    #       MentorSummary.objects.create()
#    #    elif "Learner" in user_types:
#    #       profile = create_profile(user, "Learner")
#    #       summary = get_summary(profile, "Learner")
#    #       MentorSummary.objects.create()
#    # else:
#    #    if "Mentor" in user_types:
#    #       profile = create_profile(user, "Mentor")
#    #       summary = get_summary(profile, "Mentor")
#    #       MentorSummary.objects.filter(user=user)
#    #    elif "Learner" in user_types:
#    #       profile = create_profile(user, "Learner")
#    #       summary = get_summary(profile, "Learner")
#    #       MentorSummary.object.filter()
      
# # @receiver(signals.post_save, sender=UserProfileAssest)
# # def update_summary(sender, instance, **kwargs):
# #    user_profile_assest = UserProfileAssest.object.get(id=instance.id)
# #    user_type = user_profile_assest.question_for
# #    user = user_profile_assest.user
# #    if kwargs['created']:
# #       if "Mentor" == user_type:
# #          profile = create_profile(user, "Mentor")
# #          summary = get_summary(profile, "Mentor")
# #          MentorSummary.objects.create()
# #       elif "Learner" == user_type:
# #          profile = create_profile(user, "Learner")
# #          summary = get_summary(profile, "Learner")
# #          MentorSummary.objects.create()
# #    else:
# #       if "Mentor" == user_type:
# #          profile = create_profile(user, "Mentor")
# #          summary = get_summary(profile, "Mentor")
# #          MentorSummary.objects.filter(user=user)
# #       elif "Learner" == user_type:
# #          profile = create_profile(user, "Learner")
# #          summary = get_summary(profile, "Learner")
# #          MentorSummary.object.filter()
      
