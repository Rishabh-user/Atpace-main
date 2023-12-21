from django.contrib import admin
from apps.kpi.Models.SettingReference import *
from apps.kpi.Models.Learner import *
from apps.kpi.Models.ROI import *


# Setting Reference Models

admin.site.register(Competency)
admin.site.register(WayOfLearn)
admin.site.register(BaseScore)
admin.site.register(Weightage)
admin.site.register(DataPoint)
admin.site.register(CompetencyWayOfLearn)
admin.site.register(WayOfLearnWiseCourseCode)
admin.site.register(CourseCodePattern)
admin.site.register(CompetencyParamsReferenceScore)

# Learner Models

admin.site.register(Attempt)
admin.site.register(IndividualAttemptWiseDPScore)
admin.site.register(DPWiseLearnerScore)
admin.site.register(CourseCodeWiseLearnerScore)
admin.site.register(WayOfLearnWiseLearnerScore)
admin.site.register(CourseCodeWiseLearnerAssestmentScore)
admin.site.register(CompetencyWiseLearnerScore)
admin.site.register(AttemptWiseDPSubmissionData)
admin.site.register(AttemptWiseDPLSKData)

# ROI
admin.site.register(CourseCertificationType)
admin.site.register(CourseConductedBy)
admin.site.register(CourseLevel)
admin.site.register(CoursesLaunchTimeLineCategory)
admin.site.register(CitizenType)
admin.site.register(Month)
admin.site.register(MonthCitizenTypeBasedData)
admin.site.register(TotalEmployee)
admin.site.register(NumberOfEmployee)
admin.site.register(NoActivityMenteeData)
admin.site.register(NoActivityMentorData)
admin.site.register(NoActivityPairData)
admin.site.register(MonthBasedData)
admin.site.register(SubsidyAmount)
admin.site.register(DirectHiringIncentive)
admin.site.register(SkillDevelopmentFactor)
admin.site.register(AdjustmentFactor)
admin.site.register(OrganizationOrClientData)
admin.site.register(CapexProjectSummary)
admin.site.register(TotalIncrementExistingLabel)
admin.site.register(BusinessCaseSummary)
admin.site.register(BusinessCaseKPI)
admin.site.register(CashSummary)





