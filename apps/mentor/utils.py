from apps.atpace_community.utils import local_time, datetime_string
from apps.mentor.models import mentorCalendar, AssignMentorToUser
from apps.users.models import Mentor
from datetime import *
from django.db.models.query_utils import Q

def check_user_slots(user):
    assign_mentors = AssignMentorToUser.objects.filter(user=user, is_assign=True, is_revoked=False).values("mentor").distinct()
    available_slot_list = []
    for assign_mentor in assign_mentors:
        # last_7_date = datetime.today() + timedelta(days=7)
        if mentor_calendar := mentorCalendar.objects.filter(Q(start_time__date__gte=datetime.now()), is_cancel=False, slot_status="Available", mentor=assign_mentor['mentor']):
            for cal in mentor_calendar:
                mentor = Mentor.objects.get(id=assign_mentor['mentor'])
                day, time = datetime_string(local_time(cal.start_time))
                available_slot_list.append({
                    "mentor_id": mentor.id,
                    "mentor_name": f"{mentor.first_name} {mentor.last_name}",
                    "slot_timimg": local_time(cal.start_time),
                    "slot_time": f"{day}, {time}"
                })
    available_slot_list.sort(key=lambda x: x["slot_timimg"])
    return available_slot_list