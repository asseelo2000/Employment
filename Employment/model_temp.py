# class Branch(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="branch_user")
#     branch_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=10)
#     image = models.ImageField(upload_to="branchs/images/", blank=True, null= True)
#     type = models.CharField(max_length=15, choices=[('English Section', 'English Section'), ('Arabic Section', 'Arabic Section')], default='Arabic')
#     status = models.CharField(max_length=15, choices=[('Employing', 'Employing'), ('Not Employing', 'Not Employing')], default='Not Employing')

#     def __str__ (self):
#         return self.user.username

# class JobOpening(models.Model):
#     title = models.CharField(max_length=255)  # اسم الوظيفة
#     description = models.TextField(default='يشبسيبسيبسيبيسبسيببيسب')  # وصف الوظيفة
#     requirements = models.TextField(default='يشبسيبسيبسيبيسبسيببيسب')  # متطلبات الوظيفة
#     work_schedule_type = models.CharField(_("Schedule Type"), max_length=15, choices=[('Full-time', 'Full-time'), ('Part-time', 'Part-time')])  # E.g., 'Full-time', 'Part-time', etc.
#     posted_date = models.DateTimeField()  # تاريخ نشر الوظيفة
#     closing_date = models.DateTimeField()
#     branch = models.ForeignKey("Branch",related_name="job_openings", on_delete=models.CASCADE, verbose_name=_("Opening Branch"))
#     is_active = models.BooleanField(_("Is avaliable"), default=True)  # حالة الوظيفة (نشطة/غير نشطة)


#     def __str__(self):
#         return self.title


# class Applicant(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="applicant")
#     phone = models.CharField(max_length=10)
#     image = models.ImageField(upload_to="applicants/images/", blank=True)
#     date_of_birth = models.DateField(null=True, blank=True)
#     address = models.TextField()
#     gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], default='Male')

#     def __str__(self):
#         return self.user.username

# class JobApplication(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="job_applications_branch")
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name="applications")
#     resume = models.FileField(upload_to='applicants/resumes/')  # رفع السيرة الذاتية
#     cover_letter = models.TextField(blank=True, null=True)  # رسالة التغطية
#     applied_date = models.DateTimeField(auto_now_add=True)  # تاريخ التقديم
#     application_platform = models.CharField(
#         max_length=50,
#         choices=[
#             ('portal', 'Portal'),
#             ('email', 'Email'),
#             ('social_media', 'Social Medial'),
#             ('in_person', 'In Person')
#                             ],
#         default='portal'
#     )
#     status = models.CharField(
#         max_length=50,
#         choices=[
#             ('received', 'Received'),
#             ('under_review', 'Under Review'),
#             ('shortlisted', 'Shortlisted'),
#             ('rejected', 'Rejected'),
#             ('hired', 'Hired') 
#         ],
#         default='received'
#     )  # حالة الطلب

#     def __str__(self):
#         return f"{self.applicant.user.username} - {self.job_opening.title}"

# class RecruitmentCampaign(models.Model):
#     name = models.CharField(max_length=255)  # اسم الحملة
#     description = models.TextField()  # وصف الحملة
#     start_date = models.DateField()  # تاريخ بدء الحملة
#     end_date = models.DateField()  # تاريخ انتهاء الحملة
#     organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # منظم الحملة
#     job_openings = models.ManyToManyField(JobOpening, related_name='campain_jobopenings')  # الوظائف التي يتم التوظيف لها خلال الحملة
#     attendees_count = models.IntegerField(default=0)  # عدد الحضور المتوقع
#     campain_address = models.CharField(max_length=50, default='sanaa')
#     location = PlainLocationField(based_fields=["campain_address"], zoom=14, default='')
#     is_active = models.BooleanField(default=True)  # حالة الحملة (نشطة/غير نشطة)

#     def __str__(self):
#         return self.name

# class PreEmploymentTest(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # المتقدم للوظيفة
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE)  # الوظيفة الشاغرة المرتبطة
#     test_type = models.CharField(
#         max_length=50,
#         choices=[('technical', 'Technical'), ('personality', 'Personality'), ('group', 'Group')],
#         default='technical'
#     )  # نوع الاختبار
#     score = models.DecimalField(max_digits=5, decimal_places=2)  # درجة الاختبار
#     test_date = models.DateTimeField(auto_now_add=True)  # تاريخ الاختبار
#     result = models.CharField(
#         max_length=50,
#         choices=[('pass', 'Pass'), ('fail', 'Fail')],
#         default='pending'
#     )  # نتيجة الاختبار

#     def __str__(self):
#         return f"Test for {self.applicant.user.username} - {self.job_opening.title} - {self.test_type}"

    # def clean(self):
    #     super().clean()
    #     try:
    #         application = JobApplication.objects.get(applicant=self.applicant, job_opening=self.job_opening)
    #         if application.status != JobApplicationStatus.SHORTLISTED:
    #             raise ValidationError("Applicant must be shortlisted for an interview.")
    #         pre_employment_test = PreEmploymentTest.objects.get(applicant=self.applicant, job_opening=self.job_opening)
    #         if pre_employment_test.result != TestResult.PASS:
    #             raise ValidationError("Applicant must pass the pre-employment test for an interview.")
    #     except JobApplication.DoesNotExist:
    #         raise ValidationError("Job application does not exist for this applicant and job opening.")

    # def __str__(self):
    #     return f"{self.applicant.user.get_full_name()} - {self.job_opening.title} - {self.interview_date}"

# class Interview(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # المتقدم للوظيفة
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE)  # الوظيفة الشاغرة المرتبطة
#     interview_date = models.DateTimeField()  # تاريخ المقابلة
#     interview_mode = models.CharField(
#         max_length=50,
#         choices=[('online', 'Online'), ('in_person', 'In Person')],
#         default='in_person'
#     )  # نوع المقابلة
#     interview_address = models.CharField(max_length=50, default='sanaa')
#     interview_location = PlainLocationField(based_fields=["campain_address"], zoom=14, default=interview_address)
#     interviewer = models.ManyToManyField(User, related_name='interviewers')  # المسؤولون عن المقابلة
#     feedback = models.TextField(blank=True, null=True)  # ملاحظات المقابلة

#     def __str__(self):
#         return f"{self.applicant.user.username} - {self.job_opening.title} - {self.interview_date}"


# class ApplicantEvaluation(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # المتقدم للوظيفة
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE)  # الوظيفة الشاغرة المرتبطة
#     skills_score = models.DecimalField(max_digits=5, decimal_places=2)  # the skills_score limit is 10, for example 8/10 or 10/10, should not exceed 10
#     experience_score = models.DecimalField(max_digits=5, decimal_places=2)  # the experience_score limit is 10, for example 8/10 or 10/10, should not exceed 10
#     interview_score = models.DecimalField(max_digits=5, decimal_places=2)  # the interview_score limit is 10, for example 8/10 or 10/10, should not exceed 10
#     overall_score = models.DecimalField(max_digits=5, decimal_places=2)  # # the overall_score should be caluculated as an average of skills_score+experience_score+interview_score, and its limit is 30, for example 27/30 or 30/30, should not exceed 30
#     evaluation_date = models.DateTimeField(auto_now_add=True)  # تاريخ التقييم
#     evaluator = models.ForeignKey(User, related_name='evaluator', on_delete=models.SET_NULL, null=True)  # المسؤول عن التقييم

#     def __str__(self):
#         return f"{self.applicant.user.username} - {self.job_opening.title}"

# class JobOffer(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # المتقدم للوظيفة
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE)  # الوظيفة الشاغرة المرتبطة
#     offer_date = models.DateTimeField(auto_now_add=True)  # تاريخ تقديم العرض
#     salary_offered = models.DecimalField(max_digits=10, decimal_places=2)  # الراتب المقدم
#     benefits = models.TextField()  # المزايا الممنوحة
#     status = models.CharField(
#         max_length=50,
#         choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
#         default='pending'
#     )  # حالة العرض
#     negotiation_notes = models.TextField(blank=True, null=True)  # ملاحظات التفاوض (اختياري)
#     final_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # الراتب النهائي بعد التفاوض (إن وجد)

#     def __str__(self):
#         return f"{self.applicant.user.username} - {self.job_opening.title} - {self.status}"

# class Onboarding(models.Model):
#     employee = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # الموظف الجديد
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.SET_NULL, null=True)  # الوظيفة الشاغرة المرتبطة
#     hiring_date = models.DateField()  # تاريخ التعيين
#     contract_signed = models.BooleanField(default=False)  # حالة توقيع العقد
#     onboarding_completion = models.BooleanField(default=False)  # حالة إتمام إجراءات الإدماج
#     orientation_date = models.DateField(null=True, blank=True)  # تاريخ التوجيه
#     assigned_mentor = models.ForeignKey(User, related_name='mentor', on_delete=models.SET_NULL, null=True)  # الموظف الموجه

#     def __str__(self):
#         return f"{self.employee.user.username} - {self.job_opening.title}"


# class ApplicantTracking(models.Model):
#     applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)  # المتقدم للوظيفة
#     job_opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE)  # الوظيفة المرتبطة
#     application_status = models.CharField(
#         max_length=50,
#         choices=[
#             ('applied', 'Applied'),
#             ('under_review', 'Under Review'),
#             ('interview_scheduled', 'Interview Scheduled'),
#             ('offered', 'Offered'),
#             ('hired', 'Hired'),
#             ('rejected', 'Rejected')
#         ],
#         default='applied'
#     )  # حالة الطلب
#     tracking_date = models.DateTimeField(auto_now_add=True)  # تاريخ التحديث الأخير لحالة المتقدم
#     notes = models.TextField(blank=True, null=True)  # ملاحظات إضافية حول حالة المتقدم

#     def __str__(self):
#         return f"{self.applicant.user.username} - {self.job_opening.title} - {self.application_status}"