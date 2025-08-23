from django.contrib import admin
from .models import NurseProfile, Shift, ShiftRequest, UserProfileSchedulingRule

@admin.register(NurseProfile)
class NurseProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'position']

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['nurse', 'date', 'shift_type']

@admin.register(ShiftRequest)
class ShiftRequestAdmin(admin.ModelAdmin):
    list_display = ['nurse', 'date', 'shift_type', 'status']

@admin.register(UserProfileSchedulingRule)
class UserProfileSchedulingRuleAdmin(admin.ModelAdmin):
    list_display = ['description']
