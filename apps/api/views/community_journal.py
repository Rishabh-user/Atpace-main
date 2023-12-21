from apps.api.serializers import UpdateJournalSerializer, UserIdSerializer
from apps.api.utils import update_boolean
from apps.atpace_community.utils import avatar
from apps.community.models import LearningJournals, LearningJournalsComments, WeeklyLearningJournals
from apps.content.models import Content
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from apps.users.models import User
from notifications import notify
from apps.community.utils import CommunityAllSpaces
from apps.content.models import Channel
from rest_framework.permissions import AllowAny

# API for creating learning/weekly journal and updating learning journal for journey


class UpdateLearningJournal(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = UpdateJournalSerializer(data=request.data)
        if serializer.is_valid():
            is_weekly_journal = False
            weekely_journal_id = ""
            is_private = False
            is_draft = update_boolean(data['is_draft'])
            try:
                user = User.objects.get(pk=data['user_id'])
            except User.DoesNotExist:
                return Response({"message": "Invalid User",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            if request.data['type'] == "Learning":
                is_private = data['is_private']
                try:
                    content = Content.objects.get(pk=data['quest_id'])
                    name = content.title + "- Learning Journal"
                except Content.DoesNotExist:
                    return Response({"message": "Invalid Quest",  "success": False}, status=status.HTTP_404_NOT_FOUND)
            else:
                is_weekly_journal = True
                weekely_journal_id = request.data['quest_id']
                name = "Weekely Journal"

            learning_journal = data['learning_journal']

            user_name = f"{user.first_name} {user.last_name}"

            if data['id'] == 0:

                getlearning_journal = LearningJournals.objects.create(name=name, user_name=user_name, user_id=user.pk,  email=user.email, is_weekly_journal=is_weekly_journal, weekely_journal_id=weekely_journal_id,
                                                                      learning_journal=learning_journal, is_draft=is_draft, is_private=is_private, microskill_id=data['quest_id'], journey_id=data['journey_id'])
            else:
                getlearning_journal = LearningJournals.objects.filter(pk=data['id'])
                if not getlearning_journal:
                    return Response({"message": "Invalid Journal Id", "success": False}, status=status.HTTP_404_NOT_FOUND)
                getlearning_journal = getlearning_journal.first()
                print("user_id ",getlearning_journal.user_id)
                if str(getlearning_journal.user_id) == str(user.id):
                    if request.data['type'] == "Learning":
                        getlearning_journal.learning_journal = learning_journal
                        getlearning_journal.is_private = update_boolean(data['is_private'])
                        getlearning_journal.save()
                    elif getlearning_journal.is_draft == True:
                        getlearning_journal.learning_journal = learning_journal
                        getlearning_journal.is_draft = is_draft
                        getlearning_journal.save()
                    else:
                        return Response({"message": "Journal can not be updated", "success": False}, status=400)
                else:
                    return Response({"message": "You are not authorised to update the journal", "success": False}, status=400)

            response = {
                "message": "Success",
                "success": True,
                "data": {
                    "id": getlearning_journal.id,
                    "learning_journal": getlearning_journal.learning_journal
                }

            }
            return Response(response, status=200)
        return Response({"message": serializer.errors,  "success": False}, status=400)


class AllJournal(APIView):
    def post(self, request):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():

            user = User.objects.get(pk=request.data['user_id'])
            notify.send(user, recipient=user, verb='New Journal Created Successfully Successfully.')
            learning_journal = LearningJournals.objects.filter(email=user.email)
            if data.get('journey_id'):
                journey_id = request.data['journey_id']
                learning_journal = learning_journal.filter(journey_id=journey_id)
            print(learning_journal)
            learning_journal_list = []
            for learning_journal in learning_journal:
                comments_list = []
                for comments in LearningJournalsComments.objects.filter(learning_journal=learning_journal):
                    comments_list.append({
                        "learning_journal_id": comments.learning_journal.pk,
                        "comment": comments.body,
                        "user_name": comments.user_name,
                        "user_id": comments.user_id,
                        "created_at": learning_journal.created_at,
                        "updated_at": learning_journal.updated_at,
                    })

                learning_journal_list.append({
                    "id": learning_journal.pk,
                    "name": learning_journal.name,
                    "quest_id": learning_journal.microskill_id,
                    "learning_journal": learning_journal.learning_journal,
                    "journey_id": learning_journal.journey_id,
                    "user_name": learning_journal.user_name,
                    "created_at": learning_journal.created_at,
                    "updated_at": learning_journal.updated_at,
                    "comments": comments_list
                })
            response = {
                "message": "Success",
                "success": True,
                "data": learning_journal_list

            }
            return Response(response, status=200)

        return Response({"message": serializer.errors,  "success": False}, status=400)


class WeekelyJournals(APIView):
    def post(self, request):
        data = request.data
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            id = request.data['journal_id']
            journey_id = request.data['journey_id']
            user = User.objects.get(pk=request.data['user_id'])
            learning_journals = LearningJournals.objects.filter(
                journey_id=journey_id, email=user.email, weekely_journal_id=id).first()
            print("learning_journals", learning_journals)
            comments = LearningJournalsComments.objects.filter(
                learning_journal=learning_journals).order_by("-created_at")
            comment_list = []
            for comment in comments:
                commentor = User.objects.filter(id=comment.user_id)
                comment_list.append({'id': comment.id, 'user_email': comment.user_email, 'user_name': comment.user_name, "profile_image": avatar(commentor.first()) if commentor else "",
                                     'user_id': comment.user_id, 'body': comment.body, 'parend_comment_id': comment.parent_comment_id, "created_at": comment.created_at})

            post_user = ''
            if learning_journals:
                post_user = User.objects.filter(id=learning_journals.user_id)
            learning_journals_list = {
                "id": learning_journals.id if learning_journals else 0,
                "name": learning_journals.name if learning_journals else "",
                "learning_journal": learning_journals.learning_journal if learning_journals else "",
                "comments": comment_list,
                "profile_image": avatar(post_user.first()) if post_user else "",
                "user_name": learning_journals.user_name if learning_journals else "",
                "created_at": learning_journals.created_at if learning_journals else "",
                'is_draft': learning_journals.is_draft if learning_journals else "",
            }
            try:
                weekely_journal = WeeklyLearningJournals.objects.get(id=id)
            except WeeklyLearningJournals.DoesNotExist:
                return Response({"message": "journal_id or journey_id is not valid", "success": False}, status=status.HTTP_404_NOT_FOUND)
            data = {
                "journal_id": weekely_journal.id,
                "learning_journal": weekely_journal.learning_journal
            }
            response = {
                "message": "Success",
                "success": True,
                "data": {
                    "template": data,
                    "journal_data": learning_journals_list
                }

            }
            return Response(response, status=200)

        return Response({"message": serializer.errors,  "success": False}, status=400)


class CommunityList(APIView):
    def get(self, request, user_id):
        data = {"user_id": str(user_id)}
        serializer = UserIdSerializer(data=data)
        if serializer.is_valid():
            community_id = "22900"
            all_spaces = CommunityAllSpaces(community_id)
            response = {
                "message": "Success",
                "success": True,
                "data": all_spaces

            }

            return Response(response, status=200)
        return Response({"message": serializer.errors,  "success": False}, status=400)


class JourneyJournal(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        print("Hello Shru!")
        try:
            journey = Channel.objects.get(id=self.kwargs['journey_id'])
        except Channel.DoesNotExist:
            return Response({"message": "Journey doesn't exist", "success": False}, status=status.HTTP_404_NOT_FOUND)

        journals = LearningJournals.objects.filter(journey_id=journey.id, is_weekly_journal=True)
        journal_list = []
        for journal in journals:
            journal_list.append({
                "id": journal.id,
                "name": journal.name,
                "content": journal.learning_journal,
                "journey_id": journal.journey_id,
                "is_draft": journal.is_draft
            })
        response = {
            "message": "Journey journal response",
            "success": True,
            "data": journal_list
        }
        return Response(response, status=status.HTTP_200_OK)

