import ast
import googletrans
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import Mentor, Company
from apps.mentor_panel.models import MentorMarketPlace, WorkExperience, MentorMarketPlaceCertificates, MentorMarketPlaceEducation, MentoringTypes, TargetAudience
from apps.atpace_community.utils import certificate_image
from apps.mentor_panel.serializers import EmailForInvitingSerializer, MentorCertificateSerializers, PostAdvanceProfileSerilizer, PublishOnMarketPlaceSerializer, WorkExperienceSerializers, MentorEducationSerializer
from apps.api.utils import check_valid_user, update_boolean
from apps.users.utils import marketplace_user_email
from ravinsight.constants import certification_level, contact_preferences, location_types, employment_types
from rest_framework.permissions import AllowAny
# Get all the marketplace profile data
class MentorAdvanceProfile(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        
        try:
            mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {}

        if profile_data := MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first():
            mentoring_types_obj = profile_data.mentoring_types.all()
            target_audience_obj = profile_data.target_audience.all()

            mentoring_types = [{"id": types.id, "name": types.name} for types in mentoring_types_obj]

            target_audience = [{"id": types.id, "name": types.name} for types in target_audience_obj]

            work_experience_obj = WorkExperience.objects.filter(user=mentor, is_active=True, is_delete=False).order_by('-created_at')
            work_experience = [{
                "id": experience.id,
                "user_id": experience.user.id,
                "company": experience.company,
                "designation": experience.designation,
                "start_date": experience.start_date,
                "currently_working": experience.currently_working,
                "end_date": experience.end_date,
                "location": experience.location,
                "location_type": experience.location_type,
                "employment_type": experience.employment_type,
                "description": experience.description
            } 
                for experience in work_experience_obj]


            certificates_obj = MentorMarketPlaceCertificates.objects.filter(user=mentor, is_active=True, is_delete=False)
            certificates = [{
                "id": certificate.id,
                "user_id": certificate.user.id,
                "title": certificate.title,
                "certificate": certificate_image(certificate),
                "certification_level": certificate.certification_level,
                "generated_date": certificate.generated_date,
                "is_expiration_date": certificate.is_expiration_date,
                "valid_upto": certificate.valid_upto,
                "description": certificate.description
            }
                for certificate in certificates_obj]

            data = {
                "id" : mentor.id,
                "name" : mentor.get_full_name(),
                "mentoring_style" : profile_data.mentoring_style,
                "mentoring_types" : mentoring_types,
                "target_audience" : target_audience,
                "languages": profile_data.languages.split(","),
                "total_experience": profile_data.total_experience,
                "contact_preferences" : profile_data.contact_preferences.split(","),
                "partner_badge_id" : profile_data.partner_badge.id,
                "partner_badge_name" : profile_data.partner_badge.name,
                "keep_contact_details_private" : profile_data.keep_contact_details_private,
                "location" : profile_data.location,
                "expertise" : profile_data.expertise,
                "work_experience" : work_experience,
                "certificates": certificates,
                "linkedin_profile": mentor.linkedin_profile,
                "twitter_profile": mentor.twitter_profile,
                "facebook_profile": mentor.facebook_profile,
                "instagram_profile": mentor.instagram_profile,
                "admin_publish_on_marketplace": mentor.admin_publish_on_marketplace,
                "private_profile": mentor.private_profile,
                "feedback_score": 0,
                "mentoring_hours": 2,
                "marketplace_status": mentor.marketplace_status,
                "mentor_publish_on_marketplace": mentor.mentor_publish_on_marketplace,
            }

        response = {
            "message": "Get Mentor Advance Profile",
            "data": data,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        serializer = PostAdvanceProfileSerilizer(data=request.data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                company = Company.objects.get(id=request.data['partner_badge'])
            except Company.DoesNotExist:
                return Response({"message": "partner_badge does not exists", "success": False}, 
                status=status.HTTP_404_NOT_FOUND)

            print("request.data", request.data)

            mentor.linkedin_profile = request.data['linkedin_profile']
            mentor.twitter_profile = request.data['twitter_profile']
            mentor.instagram_profile = request.data['instagram_profile']
            mentor.facebook_profile = request.data['facebook_profile']
            mentor.private_profile = update_boolean(request.data['private_profile'])
            mentor.mentor_publish_on_marketplace = update_boolean(request.data['publish_to_marketplace'])
            mentor.marketplace_status = "In Review"
            mentor.save()
            total_experience = request.data['total_experience']
            total_experience = request.data['total_experience']

            if mentor_marketplace := MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False):
                mentor_marketplace.update(partner_badge=company, mentoring_style=request.data['mentoring_style'], languages=request.data['languages'], contact_preferences=request.data['contact_preferences'], keep_contact_details_private=update_boolean(request.data['keep_contact_details_private']), total_experience=float(total_experience))
                mentor_marketplace = mentor_marketplace.first()
                mentor_marketplace.mentoring_types.clear()
                mentor_marketplace.target_audience.clear()
                
            else:
                mentor_marketplace = MentorMarketPlace.objects.create(partner_badge=company, user=mentor, mentoring_style=request.data['mentoring_style'], languages=request.data['languages'], contact_preferences=request.data['contact_preferences'], keep_contact_details_private=update_boolean(request.data['keep_contact_details_private']), total_experience=float(total_experience))
            
            print("mentoring_types request data", request.data['mentoring_types'], type(request.data['mentoring_types']))
            mentoring_types = request.data['mentoring_types'].split(",")
            print("mentoring_types", mentoring_types, type(mentoring_types))
            for id in mentoring_types:
                mentor_marketplace.mentoring_types.add(id)
            target_audience = request.data['target_audience'].split(",")
            for audi in target_audience:
                mentor_marketplace.target_audience.add(audi)

            response = {
                "message": "Mentor Advance Profile Updated",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Get individual work experience
class GetMentorWorkEperience(APIView):

    def get(self, request, *args, **kwargs):
        try:
            mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)

        experience = WorkExperience.objects.filter(id=self.kwargs['experience_id'], user=mentor).first()
        if not experience:
            return Response({"message": "Work Experience does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": experience.id,
            "user_id": experience.user.id,
            "company": experience.company,
            "designation": experience.designation,
            "start_date": experience.start_date,
            "currently_working": experience.currently_working,
            "end_date": experience.end_date,
            "location": experience.location,
            "location_type": experience.location_type,
            "employment_type": experience.employment_type,
            "description": experience.description
        }

        response = {
            "message": "Get Mentor Work Experience",
            "data": data,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = WorkExperienceSerializers(data=request.data)
        if serializer.is_valid():
            try:
                user = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user.marketplace_status = "In Review"
            user.save()
            mentor_marketplace = MentorMarketPlace.objects.filter(user=user, is_active=True, is_delete=False).first()
            if not mentor_marketplace:
                return Response({"message": "Mentor Marketplace does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                work_experience = WorkExperience.objects.get(id=self.kwargs['experience_id'], user=user, market_place=mentor_marketplace, is_active=True, is_delete=False)
            except WorkExperience.DoesNotExist:
                return Response({"message": "experience_id does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            start_date = request.data['start_date']
            company = request.data['company']
            currently_working = update_boolean(request.data['currently_working'])
            location = request.data['location']
            location_type = request.data['location_type']
            designation = request.data['designation']
            employment_type=request.data['employment_type']

            work_experience.company=company
            work_experience.designation=designation
            work_experience.start_date=start_date
            work_experience.currently_working=currently_working
            work_experience.location=location
            work_experience.location_type=location_type
            work_experience.employment_type=employment_type

            if not currently_working:
                work_experience.end_date = request.data['end_date']
            if data.get('description'):
                work_experience.description = data.get('description')
            print("work exoeef", work_experience)
            work_experience.save()
            response = {
                "message": "Mentor Work Experience Updated",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        mentor.marketplace_status = "In Review"
        mentor.save()
        experience = WorkExperience.objects.filter(id=self.kwargs['experience_id'], user=mentor)
        if not experience:
            return Response({"message": "Work Experience does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        experience.update(is_active=False, is_delete=True)
        response = {
            "message": "Work Experience deleted",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class PostMentorWorkEperience(APIView):
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = WorkExperienceSerializers(data=request.data)
        if serializer.is_valid():
            try:
                user = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            user.marketplace_status = "In Review"
            user.save()
            mentor_marketplace = MentorMarketPlace.objects.filter(user=user, is_active=True, is_delete=False).first()
            start_date = request.data['start_date']
            company = request.data['company']
            currently_working = update_boolean(request.data['currently_working'])
            location = request.data['location']
            location_type = request.data['location_type']
            designation = request.data['designation']
            employment_type=request.data['employment_type']

            work_experience = WorkExperience.objects.create(market_place=mentor_marketplace,
                user=user, company=company, designation=designation, start_date=start_date, 
                currently_working=currently_working, location=location, location_type=location_type, employment_type=employment_type)
            if not currently_working:
                work_experience.end_date = request.data['end_date']
            if data.get('description'):
                work_experience.description = data.get('description')
            work_experience.save()
            response = {
                "message": "Mentor Work Experience Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Get individual certificate
class GetMentorCertificate(APIView):

    def get(self, request, *args, **kwargs):
        try:
            user = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        certificate = MentorMarketPlaceCertificates.objects.filter(id=self.kwargs['certificate_id'], user=user, is_active=True, is_delete=False).first()
        if not certificate:
            return Response({"message": "Certificate does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": certificate.id,
            "user_id": certificate.user.id,
            "title": certificate.title,
            "certificate": certificate_image(certificate),
            "certification_level": certificate.certification_level,
            "generated_date": certificate.generated_date,
            "is_expiration_date": certificate.is_expiration_date,
            "valid_upto": certificate.valid_upto,
            "description": certificate.description
        }
        response = {
            "message": "Certificate data created",
            "data": data,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = MentorCertificateSerializers(data=request.data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor.marketplace_status = "In Review"
            mentor.save()
            mentor_marketplace = MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first()
            if not mentor_marketplace:
                return Response({"message": "Mentor Marketplace does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            try:
                emp_certificate = MentorMarketPlaceCertificates.objects.get(id=self.kwargs['certificate_id'], user=mentor, is_active=True, is_delete=False)
            except MentorMarketPlaceCertificates.DoesNotExist:
                return Response({"message": "certificate_id does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            title = request.data['title']
            certificate = request.data['certificate']
            generated_date = request.data['generated_date']
            is_expiration_date = update_boolean(request.data['is_expiration_date'])
            certification_level = request.data['certification_level']
            emp_certificate.title=title
            emp_certificate.certificate=certificate
            emp_certificate.certification_level=certification_level
            emp_certificate.generated_date=generated_date
            emp_certificate.is_expiration_date=is_expiration_date
            if is_expiration_date:
                emp_certificate.valid_upto = request.data['valid_upto']
            if data.get('description'):
                emp_certificate.description = data.get('description')
            emp_certificate.save()

            response = {
                "message": "Mentor Certificate Updated",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        try:
            user = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        user.marketplace_status = "In Review"
        user.save()
        certificate = MentorMarketPlaceCertificates.objects.filter(id=self.kwargs['certificate_id'], user=user, is_active=True, is_delete=False)
        if not certificate:
            return Response({"message": "Certificate does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        certificate.update(is_active=False, is_delete=True)
        response = {
            "message": "Certificate data deleted",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)

# Get individual education
class GetMentorEducation(APIView):

    def get(self, request, *args, **kwargs):
        try:
            user = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        
        education = MentorMarketPlaceEducation.objects.filter(id=self.kwargs['education_id'], user=user, is_active=True, 
                                                                   is_delete=False).first()
        if not education:
            return Response({"message": "Education does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "id": education.id,
            "user_id": education.user.id,
            "program": education.program,
            "major": education.major,
            "university": education.university,
            "location": education.location,
            "start_date": education.start_date,
            "end_date": education.end_date,
            "is_ongoing": education.is_ongoing,
            "excellence": education.excellence,
            "description": education.description
        }
        response = {
            "message": "Education data received",
            "data": data,
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = MentorEducationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            mentor.marketplace_status = "In Review"
            mentor.save()

            mentor_marketplace = MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first()
            if not mentor_marketplace:
                return Response({"message": "Mentor Marketplace does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                emp_education = MentorMarketPlaceEducation.objects.filter(id=self.kwargs['education_id'], user=mentor, is_active=True, is_delete=False).first()
            except MentorMarketPlaceCertificates.DoesNotExist:
                return Response({"message": "certificate_id does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            program = data['program']
            major = data['major']
            university = data['university']
            location = data['location']
            start_date = data['start_date']
            end_date = data['end_date']
            is_ongoing = update_boolean(data['is_ongoing'])
                            
            if data.get('excellence'):
                emp_education.excellence = data.get('excellence')
            if data.get('description'):
                emp_education.description = data.get('description')

            emp_education.program = program
            emp_education.major = major
            emp_education.university = university
            emp_education.location = location
            emp_education.start_date = start_date
            emp_education.end_date = end_date
            emp_education.is_ongoing = is_ongoing

            emp_education.save()

            response = {
                "message": "Mentor Education Updated",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        try:
            user = Mentor.objects.get(id=self.kwargs['mentor_id'])
        except Mentor.DoesNotExist:
            return Response({"message": "Mentor does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        
        user.marketplace_status = "In Review"
        user.save()

        education = MentorMarketPlaceEducation.objects.filter(id=self.kwargs['education_id'], user=user, is_active=True, is_delete=False)

        if not education:
            return Response({"message": "Education does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND)
        education.update(is_active=False, is_delete=True)

        response = {
            "message": "Education data deleted",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


class PostMentorCertificate(APIView):
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = MentorCertificateSerializers(data=request.data)
        if serializer.is_valid():
            try:
                mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor.marketplace_status = "In Review"
            mentor.save()
            mentor_marketplace = MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first()
            title = request.data['title']
            certificate = request.data['certificate']
            generated_date = request.data['generated_date']
            is_expiration_date = update_boolean(request.data['is_expiration_date'])
            certification_level = request.data['certification_level']
            emp_certificate = MentorMarketPlaceCertificates.objects.create(user=mentor, title=title, certificate=certificate, certification_level=certification_level, generated_date=generated_date, is_expiration_date=is_expiration_date)
            if is_expiration_date:
                emp_certificate.valid_upto = request.data['valid_upto']
            if data.get('description'):
                emp_certificate.description = data.get('description')
            emp_certificate.save()

            response = {
                "message": "Mentor Certificate Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostMentorEducation(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = MentorEducationSerializer(data=request.data)
        if serializer.is_valid():

            try:
                mentor = Mentor.objects.get(id=self.kwargs['mentor_id'])
            except Mentor.DoesNotExist:
                return Response({"message": "user does not exists", "success": False}, status=status.HTTP_404_NOT_FOUND)
            
            mentor.marketplace_status = "In Review"
            mentor.save()
            mentor_marketplace = MentorMarketPlace.objects.filter(user=mentor, is_active=True, is_delete=False).first()

            program = data['program']
            major = data['major']
            university = data['university']
            location = data['location']
            start_date = data['start_date']
            end_date = data['end_date']
            is_ongoing = update_boolean(data['is_ongoing'])
                            
            emp_education = MentorMarketPlaceEducation.objects.create(user=mentor, market_place=mentor_marketplace, program=program, 
                                                                      major=major, university=university, location=location, 
                                                                      start_date=start_date, end_date=end_date, is_ongoing=is_ongoing)
            if data.get('excellence'):
                emp_education.excellence = data.get('excellence')
            if data.get('description'):
                emp_education.description = data.get('description')

            emp_education.save()
            response = {
                "message": "Mentor Education Created",
                "success": True,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Get Mentor Skills/Exeprtise
class UserSkillSet(APIView):

    def get(self, request, *args, **kwargs):
        
        response = {
            "message": "Get Mentor Skills",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        
        response = {
            "message": "Update Mentor Skills",
            "success": True,
        }
        return Response(response, status=status.HTTP_200_OK)

#get advance profile constant data for selecting dropdown
class ProfileConstantData(APIView):
    def get(self, request, *args, **kwargs):
        certification_level_list = contact_preferences_list = location_types_list = employment_types_list = []
        target_audience_list = mentoring_types_list = language_list = []

        if self.request.query_params.get('certification_level'):
            certification_level_list = [level[0] for level in certification_level]
        if self.request.query_params.get('contact_preferences'):
            contact_preferences_list = [level[0] for level in contact_preferences]
        if self.request.query_params.get('location_types'):
            location_types_list = [type[0] for type in location_types]
        if self.request.query_params.get('employment_types'):
            employment_types_list = [type[0] for type in employment_types]
        if self.request.query_params.get('target_audience'):
            target_audience = TargetAudience.objects.all()
            target_audience_list = [{
                "id": audience.id,
                "name": audience.name
            }
                for audience in target_audience]
        if self.request.query_params.get('mentoring_types'):
            mentoring_types = MentoringTypes.objects.all()
            mentoring_types_list = [{
                "id": type.id,
                "name": type.name
            }
                for type in mentoring_types]
        if self.request.query_params.get('languages'):
            language_list = googletrans.LANGUAGES.values()

        response = {
            "message": "Profile constant data for dropdown",
            "success": True,
            "certification_level": certification_level_list,
            "contact_preferences": contact_preferences_list,
            "location_types": location_types_list,
            "employment_types": employment_types_list,
            "target_audience": target_audience_list,
            "mentoring_types": mentoring_types_list,
            "languages": language_list,
        }
        return Response(response, status=status.HTTP_200_OK)
    
class MarketplaceInviteEmail(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EmailForInvitingSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(request.data['user_id'])
            if not user:
                return Response({"message": "User not valid", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor = Mentor.objects.filter(id=request.data['mentor_id'])
            if not mentor.first():
                return Response({"message": "User not valid", "success": False}, status=status.HTTP_404_NOT_FOUND)
            marketplace_user_email(mentor.first())
            mentor.update(marketplace_status="Pending")
            return Response({"message": "Mentor marketplace invite email sent successfully!", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)
    
class PublishOnMarketPlace(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PublishOnMarketPlaceSerializer(data=request.data)
        if serializer.is_valid():
            user = check_valid_user(request.data['user_id'])
            if not user:
                return Response({"message": "User not valid", "success": False}, status=status.HTTP_404_NOT_FOUND)
            mentor = Mentor.objects.filter(id=request.data['mentor_id'])
            if not mentor.first():
                return Response({"message": "User not valid", "success": False}, status=status.HTTP_404_NOT_FOUND)
            is_pubish = update_boolean(request.data['is_publish'])
            mentor.update(admin_publish_on_marketplace=is_pubish)
            if mentor.first().mentor_publish_on_marketplace and is_pubish:
                mentor.update(marketplace_status="Live")
                return Response({"message": "Mentor is Live on MarketPlace", "success": True}, status=status.HTTP_200_OK)
            mentor.update(marketplace_status="Approved")
            return Response({"message": "Mentor status changed and added to Approved list", "success": True}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors, "success": False}, status=status.HTTP_400_BAD_REQUEST)