from django.db import models
from django.contrib.auth.models import User

SHIFT_CHOICES = [
    ('Morning', 'Morning'),
    ('Afternoon', 'Afternoon'),
    ('Night', 'Night'),
]

class NurseProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, default='nurse')
    # def full_name(self):
    #     return f"{self.user.first_name} {self.user.last_name}"
    full_name = models.CharField(max_length=100, default='nurse')
    contract_type = models.CharField(
        max_length=20,
        choices=[('official', 'Official'), ('insured', 'Insured')]
    )
    preferred_shifts = models.JSONField(default=dict, blank=True)  # e.g., {"Monday": ["Morning", "Night"]}
    monthly_hours_required = models.PositiveIntegerField()
    ward = models.CharField(max_length=50,default='OBGYN')
    is_headnurse = models.BooleanField(default=False)


    def __str__(self):
        return self.full_name()
    
class Shift(models.Model):
    nurse = models.ForeignKey(NurseProfile, on_delete=models.CASCADE, related_name='requested_shifts',default="none")
    assigned_nurse = models.ForeignKey(NurseProfile, on_delete=models.CASCADE, related_name='assigned_shifts',default="none")
    start_time = models.DateTimeField(default="8 AM")
    end_time = models.DateTimeField(default="8 PM")
    date = models.DateField()
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES,default="MORNING")
    ward = models.CharField(max_length=50, default='OBGYN')

    class Meta:
        unique_together = ('date', 'shift_type', 'ward')

    def __str__(self):
        return f"{self.nurse} | {self.start_time} - {self.end_time}"

class ShiftRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    reason = models.TextField()
    nurse = models.ForeignKey(NurseProfile, on_delete=models.CASCADE,default="none")
    date = models.DateField()
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES,default="MORNING")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.nurse.full_name} - {self.shift} ({self.status})"
    
class SchedulingRule(models.Model):
    shift_type = models.CharField(max_length=50,default="MORNING")
    head_nurse = models.ForeignKey(User, on_delete=models.CASCADE, default="none")
    allow_post_night_off = models.BooleanField(default=True)
    max_nurses_per_shift = models.PositiveIntegerField(default=dict)  # e.g., {"Morning": 3, "Afternoon": 2, "Night": 1}
    ward = models.CharField(max_length=50, default='OBGYN')
    max_shifts_per_day = models.PositiveIntegerField(default=2)
    max_shifts_per_week = models.PositiveIntegerField(default=5)
    min_rest_hours_between_shifts = models.PositiveIntegerField(default=8)
    allow_night_shifts = models.BooleanField(default=True)


    @property
    def description(self):
        return f"Rule for {self.shift_type}"

    

    def __str__(self):
        return f"Rules for {self.ward} by {self.head_nurse.username}"
