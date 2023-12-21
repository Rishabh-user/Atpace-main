from django.db import models
import uuid


class CourseCertificationType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Label = models.CharField(max_length=20)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class CourseConductedBy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ConductedBy = models.CharField(max_length=20)
    CourseCertificationType = models.ForeignKey(CourseCertificationType, on_delete=models.CASCADE)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class CourseLevel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CourseLevelName = models.CharField(max_length=20)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class CoursesLaunchTimeLineCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TimeLine = models.CharField(max_length=20)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class CitizenType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CourseLevel = models.ForeignKey(CourseLevel, on_delete=models.CASCADE)
    TimeLine = models.ForeignKey(CoursesLaunchTimeLineCategory, on_delete=models.CASCADE)
    ConductedBy = models.ForeignKey(CourseConductedBy, on_delete=models.CASCADE)
    SubsidyInPercent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    AttemptWiseDataPointScore = models.IntegerField()
    AttemptType = models.CharField(max_length=200)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Month(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    MonthName = models.CharField(max_length=20)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class MonthCitizenTypeBasedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CitizenType = models.ForeignKey(CitizenType, on_delete=models.CASCADE)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    Absenteeism = models.IntegerField()
    Funding = models.IntegerField()
    CappedAmount = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class TotalEmployee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    TotalEmployee = models.IntegerField()
    CostPerTrainingPerEmpPerMonth = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class NumberOfEmployee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    NumberOfEmployee = models.IntegerField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class MonthBasedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    SalesForScore5 = models.IntegerField()
    SalesForScoreBW3to5 = models.IntegerField()
    SalesForScoreLessThan3 = models.IntegerField()
    TotalSales = models.IntegerField()
    EmpPlannedAsPerBudget = models.IntegerField()
    SavingVSBudget = models.IntegerField()
    CostPerEmpPerMonth = models.IntegerField()
    IncrementalEmpCostSaving = models.IntegerField()
    HiringIncentiveLimit = models.IntegerField()
    ProductivityVsExistingEmpImprovementInSales = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                                                      null=True)
    EmployeeLeavers = models.DecimalField(max_digits=5, decimal_places=2, blank=True,
                                          null=True)
    RentPerAnnum = models.IntegerField()
    ElectricityPerAnnum = models.IntegerField()

    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class SubsidyAmount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    CitizenType = models.ForeignKey(CitizenType, on_delete=models.CASCADE)
    SubsidyAmount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class DirectHiringIncentive(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Title = models.CharField(max_length=80)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    NumberOfEmployee = models.IntegerField()

    def __str__(self):
        return str(self.id)


class SkillDevelopmentFactor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    NumberOfEmpForScore5 = models.IntegerField()
    NumberOfEmpForScoreBW3to5 = models.IntegerField()
    NumberOfEmpForScoreLessThan3 = models.IntegerField()
    TotalEmployee = models.IntegerField()

    def __str__(self):
        return str(self.id)


class AdjustmentFactor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Title = models.CharField(max_length=80)
    Month = models.ForeignKey(Month, on_delete=models.CASCADE)
    AdjustmentFactor = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class OrganizationOrClientData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CompanyName = models.CharField(max_length=20)
    SalesforceLink = models.CharField(max_length=20)
    CustomerDebt = models.CharField(max_length=20)

    def __str__(self):
        return str(self.id)


class CapexProjectSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ProjectName = models.CharField(max_length=80)
    ProjectOwner = models.CharField(max_length=80)
    ProjectSpend = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ROI = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    PaybackMonth = models.IntegerField()
    NPV = models.IntegerField()
    MarketOrCountry = models.CharField(max_length=80)
    ProjectNumber = models.IntegerField()
    DepartmentName = models.CharField(max_length=20)
    ProjectDurationInMonth = models.IntegerField()

    def __str__(self):
        return str(self.id)


class TotalIncrementExistingLabel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Label = models.CharField(max_length=20)
    IsActive = models.BooleanField(default='False')

    def __str__(self):
        return str(self.id)


class BusinessCaseSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    Title = models.CharField(max_length=80)
    TotalIncrementExistingLabel = models.ForeignKey(TotalIncrementExistingLabel, on_delete=models.CASCADE)
    Amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.id)


class BusinessCaseKPI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    PaybackMonth = models.IntegerField()
    IRROverall = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    NPV = models.IntegerField()

    def __str__(self):
        return str(self.id)


class CashSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    RecurringCash = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    OneTimeCash = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    CashForPreFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    CashForPostFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TotalRevenue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    NetCashFundingForPreFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    NetCashForFundingPostFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    NetCashFundingFor5Yr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TrainingCostForPreFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TrainingCostForPostFinanceYr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TotalTrainingCostFor5Yr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.id)
