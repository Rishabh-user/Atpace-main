
from apps.users.models import Collabarate
from apps.mentor.models import mentorCalendar


def feedbackTemplateFor(recent_call):
    room_name = recent_call
    # room_name = recent_call.split('/')[1]
    data = []
    response = False
    if collabarate := Collabarate.objects.filter(url_title=room_name).first():
        print("FEED TEMPLATE FOR COLLABORATE CALL")
        template_for = "LiveCall" if collabarate.type == 'LiveStreaming' else 'GroupCall'
        template_for_id = collabarate.id
        company = collabarate.company
        journey = collabarate.journey
        response = True
        data.append({
            "template_for":template_for,
            "template_for_id":template_for_id,
            "company":company,
            "journey":journey
        })
    elif meeting := mentorCalendar.objects.filter(url_title=room_name).first():
        print("FEED TEMPLATE FOR MENTOR MENTEE CALL")
        template_for = "OneToOne"
        template_for_id = meeting.id
        company = meeting.company
        journey = meeting.journey
        response = True
        data.append({
            "template_for":template_for,
            "template_for_id":template_for_id,
            "company":company,
            "journey":journey
        })
        
    return data, response

def get_meeting_user(type, meeting_id):
    calendar_obj = mentorCalendar.objects.filter(id=meeting_id).first()
    calendar_obj.status = "Completed"
    calendar_obj.save()
    if(type == 'Mentor'):
        meeting_user = calendar_obj.participants.first()
    else:
        meeting_user = calendar_obj.mentor
    return meeting_user

def feedbackTemplateData(feedback_for_id, feedback_for):
    if feedback_for == "LiveStreaming":
        meeting = Collabarate.objects.filter(url_title=feedback_for_id, type=feedback_for).first()
        template_for = 'LiveCall'
    elif feedback_for == 'GroupStreaming':
        meeting = Collabarate.objects.filter(url_title=feedback_for_id, type=feedback_for).first()
        template_for = 'GroupCall'
    elif feedback_for == "MentorCall":
        meeting = mentorCalendar.objects.filter(url_title=feedback_for_id).first()
        template_for = 'OneToOne'
    data = {
        "template_for":template_for,
        "template_for_id":meeting.id,
        "company":meeting.company,
        "journey":meeting.journey
    }

    return data

