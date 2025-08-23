from django.db import models
import re
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from schedule.managers import UserProfileManager

class CustomUser(AbstractUser):

    phone_number = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Enter a valid phone number including country code")
    )

    def __str__(self):
        return self.username or str(self.phone_number)


SHIFT_CHOICES = [
    ('Morning', 'Morning'),
    ('Afternoon', 'Afternoon'),
    ('Night', 'Night'),
]

CONTRACT_CHOICES = [
    ('official', 'Official'),
    ('insured', 'Insured'),
]

class NurseProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, default='nurse')
    full_name = models.CharField(max_length=100, default='nurse')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_CHOICES)
    preferred_shifts = models.JSONField(default=dict, blank=True)  # e.g., {"Monday": ["Morning", "Night"]}
    monthly_hours_required = models.PositiveIntegerField()
    ward = models.CharField(max_length=50,default='OBGYN')
    is_headnurse = models.BooleanField(default=False)


    def __str__(self):
        return self.full_name()
    
class Shift(models.Model):
    title = models.CharField(max_length=200, default='Morning Shift')
    nurse = models.ForeignKey(
        NurseProfile, on_delete=models.CASCADE,
        related_name='requested_shifts', null=True, blank=True
    )
    assigned_nurse = models.ForeignKey(
        NurseProfile, on_delete=models.CASCADE, 
        related_name='assigned_shifts', null=True, blank=True
    )
    start_time = models.TimeField(default="08:00")
    end_time = models.TimeField(default="20:00")
    date = models.DateField()
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES,default="MORNING")
    ward = models.CharField(max_length=50, default='OBGYN')

    class Meta:
        unique_together = ('date', 'shift_type', 'ward')

    def __str__(self):
        return f"{self.title} | {self.date} | {self.shift_type}"

class ShiftRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    nurse = models.ForeignKey(NurseProfile, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    date = models.DateField()
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES,default="MORNING")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.nurse.full_name} - {self.shift} ({self.status})"
    
class UserProfileSchedulingRule(models.Model):
    shift_type = models.CharField(max_length=50,default="MORNING")
    head_nurse = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    allow_post_night_off = models.BooleanField(default=True)
    max_nurses_per_shift = models.PositiveIntegerField(default=3)  # e.g., {"Morning": 3, "Afternoon": 2, "Night": 1}
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

