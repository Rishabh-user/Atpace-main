SON = 'Son'
USER = 'user'
STOP = 'Stop'
DROP = 'Drop'
BLACK = 'Black'
PAUSE = 'Pause'
CANCEL = 'Cancel'
UNSEEN = 'unseen'
DELETED = 'Deleted'
FATHER = 'Father'
SPOUSE = 'Spouse'
MOTHER = 'Mother'
PENDING = 'Pending'
DRAFT = 'Draft'
BROTHER = 'Brother'
VERIFIED = 'verified'
FAVORITE = 'Favorite'
COMPLETE = 'Complete'
DAUGHTER = 'Daughter'
BUDGET = 'Budget'
FIND = 'Find'
SELECT = 'Select'
IGNORE = 'Ignore'
HOLD = 'Hold'
COMPLETED = 'Completed'
ACCEPTED = 'Accepted'
REJECTED = 'Rejected'
CANCELLED = 'Cancelled'
PUBLIC = 'Public'
PRIVATE = 'Private'
LIVE = 'Live'
Text = 'Text'
Image = 'Image'
Link = 'Link'
Video = 'Video'
Pdf = 'Pdf'
Quiz = 'Quiz'
Poll = 'Poll'
onlyCommunity = 'onlyCommunity'
Course = 'Course'
SkillDevelopment = 'SkillDevelopment'
SelfPaced = 'SelfPaced'
SurveyCourse = 'SurveyCourse'
MentoringJourney = "MentoringJourney"
Space_Group_ID = "587d7257-a58e-424c-83b9-3b6d8b798a3e"

RecordTypeStatus = (
    ('LearningJournal', "Learning Journal"),
    ('AskQuestion', "Ask Question"),
)

RecordFor = (
    ('Circle', 'Circle'),
    ('Atpace', 'Atpace')
)
Content_Type = (
    (Text, "Text"),
    (Image, "Image"),
    (Link, "Link"),
    (Video, "Video"),
    (Pdf, "Pdf"),
    (Quiz, 'Quiz'),
    (Poll, 'Poll'),
    ("YtVideo", "YtVideo"),
    ("Activity", "Activity")
)

Activity_Type = (
    ("CaseStudy", "Case Study"),
    ("Research", "Research"),
    ("BusinessPresentation/Assignment", "Business Presentation/Assignment"),
    ("VideoDocumentary", "Video Documentary"),
)

Channel_type = (
    # (onlyCommunity, 'Only Community'),
    (MentoringJourney, "Mentoring Journey"),
    # (Course, 'Courses'),
    (SelfPaced, 'Self Paced'),
    (SkillDevelopment, 'Skill Development Course')
)

Content_Status = (
    (LIVE, "Live"),
    (PENDING, "Pending"),
    (DRAFT, "Draft"),
)

Channel_For = (
    ("Default", "Default"),
    ("Beginner", "Beginner"),
    ("Expert", "Expert"),
    ("Intermediate", "Intermediate"),
    ("Advanced", "Advanced"),
)

Channel_Level_Type = (
    ("Assessment", "Assessment"),
    ("Survey", "Survey")
)

UserCourseStatus = (
    ("Enroll", "Enroll"),
    ("InProgress", "InProgress"),
    ('Complete', "Complete")
)


UserReadContentDataStatus = (
    ("InProgress", "InProgress"),
    ('Complete', "Complete")
)

Question_Type = (
    ("ShortAnswer", "ShortAnswer"),
    ("MultiChoice", "MultiChoice"),
    ("Checkbox", "Checkbox"),
    ("Date", "Date"),
    ("Time", "Time"),
    ("DropDown", "DropDown"),
    ("Paragraph", "Paragraph"),
    ("MultiChoiceGrid", "MultiChoice Grid"),
    ("CheckboxGrid", "Checkbox Grid"),
    ("FileUpload", "File Upload"),
    ("LinearScale", "Linear Scale")
)

skill_level = (
    ("Beginner", "Beginner"),
    ("Expert", "Expert"),
    ("Intermediate", "Intermediate"),
    ("Advanced", "Advanced"),
)

gender = (
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
)


Pool_Choice = (
    ("Tags", "Tags"),
    ("Industry", "Industry"),
    ("ALL", "All"),
)

Privacy_types = (
    ("Private", "Private"),
    ("Public", "Public"),
)


types = (
    ("Post", "Post"),
    ("Comment", "Comment"),
)

report_types = (
    ("Inappropriate Post", "Inappropriate Post"),
    ("Content Not Relatable", "Content Not Relatable"),
    ("Supporting or promoting a hate group", "Supporting or promoting a hate group"),
    ("Self-Promotion", "Self-Promotion"),
)

MentorMatchingQuestions = [
    "If you have someone in mind, that you would like to have as your Mentee in this program please enter name below",
    "Please share with us, 3 Goals you would like to achieve during this 3-month Mentoring (& Guidance) Program as a MENTOR? Please be as specific as possible & list in order of priority.",
    "Mention your Industry in the best way possible (check one below)",
    "If you have selected Other Industry above please provide details"
]

MenteeMatchingQuestions = [
    "If you have someone in mind, that you would like to have as your Mentor in this program please enter name below",
    "Please share with us, 3 Goals (BE SPECIFIC & LIST THESE IN ORDER OF PRIORITY) you would like to achieve during this 3-month Mentoring (& Guidance) Program as a MENTEE",
    "Mention your Industry in the best way possible (check one below)",
    "If you have selected Other Industry above please provide details"
]

period_type = (
    ("Days", "Days"),
    ("Month", "Month"),
    ("Months", "Months"),
    ("Year", "Year"),
    ("Years", "Years"),
    ("Unlimited", "Unlimited"),
)

LANGUAGES = {
                'zh-cn': 'chinese (simplified)',
                'zh-tw': 'chinese (traditional)',
                'en': 'english',
                'fr': 'french',
                'nl': 'dutch',
                'hi': 'hindi',
                'id': 'indonesian',
                'vi': 'vietnamese',
                'th': 'thai'
            }

template_choice =  (
        # ("Assessment", "Assessment"),
        # ("CourseCompletion", "CourseCompletion"),
        ("GroupCall", "GroupCall"),
        ("LiveCall", "LiveCall"),
        ("OneToOne", "OneToOne"),
        # ("SkillCompletion", "SkillCompletion"),
        # ("MicroSkill", "MicroSkill"),
        # ("Survey", "Survey"),
        # ("MentoringJournals", "MentoringJournals"),
        # ("Mentor", "Mentor Profile"),
        # ("Mentee", "Mentee Profile"),
    )

certification_level = (
    ('Beginner', 'Beginner'),
    ('Intermediate', 'Intermediate'),
    ('Advance', 'Advance'),
    ('Expert', 'Expert')
)

contact_preferences = (
    ("Email","Email"),
    ("Whatsapp","Whatsapp"),
    ("Telegram","Telegram"),
    ("Zoom","Zoom")
)

location_types = (
    ("Work From Office", "Work From Office"),
    ("Work From Home", "Work From Home")
)

employment_types = (
    ("Full Time", "Full Time"),
    ("Part Time", "Part Time"),
    ("Contract", "Contract"),
    ("Freelance", "Freelance")
)

recurring_choices = (
    ("Daily", "Daily"),
    ("Weekly", "Weekly"),
    ("Monthly", "Monthly"),
)

task_status_choices = (
    ("Not Started", "Not Started"),
    ("In Progress", "In Progress"),
    ("Done", "Done")
)

rsvp_choices = (
    ("Yes", "Yes"),
    ("No", "No"),
    ("May be", "May be"),
)

meet_type = (
    ("LiveStreaming", "LiveStreaming"),
    ("GroupStreaming", "GroupStreaming"),
    ("MentorCall", "MentorCall"),
    ("Event", "Event"),
    ("Other", "Other")
)