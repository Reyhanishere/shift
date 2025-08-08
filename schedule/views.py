from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegisterForm, NurseProfileForm, ShiftRequestForm
from .models import Shift, NurseProfile, ShiftRequest, SchedulingRule
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

SHIFT_CHOICES = [
    ('morning', 'Morning'),
    ('evening', 'Evening'),
    ('night', 'Night'),
]

def home(request):
    return render(request, 'schedule/home.html')  # You need to create this template

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your account has been created. You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'schedule/register.html', {'form': form})

@login_required
def nurse_dashboard(request):
    user = request.user
    shifts = Shift.objects.filter(nurse=user)
    return render(request, 'schedule/nurse_dashboard.html', {'shifts': shifts})

@login_required
def headnurse_dashboard(request):
    all_shifts = Shift.objects.all()
    return render(request, 'schedule/headnurse_dashboard.html', {'shifts': all_shifts})


def register_nurse(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        position = request.POST['position']
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        nurse_profile = NurseProfile.objects.create(user=user, full_name=full_name, position=position)
        messages.success(request, 'Registration successful. Please log in.')
        return redirect('login')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('nurse_dashboard')  # change to your desired redirect
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def edit_profile(request):
    profile, created = NurseProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = NurseProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('nurse_dashboard')  # or wherever you want
    else:
        form = NurseProfileForm(instance=profile)

    return render(request, 'schedule/edit_profile.html', {'form': form})

@login_required
def submit_shift_request(request):
    if request.method == 'POST':
        form = ShiftRequestForm(request.POST)
        if form.is_valid():
            shift_request = form.save(commit=False)
            shift_request.nurse = request.user.nurseprofile
            shift_request.save()
            return redirect('nurse_dashboard')  # یا هر صفحه‌ای که دوست داری
    else:
        form = ShiftRequestForm()

    return render(request, 'schedule/submit_shift_request.html', {'form': form})

@login_required
def view_schedule(request):
    nurse = request.user
    shifts = Shift.objects.filter(assigned_nurse=nurse).order_by('date')
    return render(request, 'schedule/view_schedule.html', {'shifts': shifts})

@login_required
def shift_calendar(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        nurse = request.user
        shifts = Shift.objects.filter(assigned_nurse=nurse).order_by('date')
        events = []
        for shift in shifts:
            events.append({
                'title': f'{shift.shift_type} Shift',
                'start': shift.date.isoformat(),
                'allDay': True,
            })
        return JsonResponse(events, safe=False)

    return render(request, 'schedule/calendar.html')


def shift_detail(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    nurses = NurseProfile.objects.all()  # بعداً می‌تونیم فیلتر کنیم براساس دسترسی و صلاحیت
    return render(request, 'schedule/shift_detail.html', {
        'shift': shift,
        'nurses': nurses,
    })

def is_headnurse(user):
    return user.is_authenticated and hasattr(user, 'nurseprofile') and user.nurseprofile.is_headnurse


@login_required
@user_passes_test(is_headnurse)
def generate_schedule(request):
    rules = SchedulingRule.objects.first()
    if not rules:
        messages.error(request, "Scheduling rules are not set.")
        return redirect('headnurse_dashboard')

    requests = ShiftRequest.objects.all().order_by('date', 'shift_type')
    assigned = []

    for req in requests:
        # بررسی اینکه آیا این پرستار قبلاً شیفت در همان تاریخ دارد
        existing = Shift.objects.filter(nurse=req.nurse, date=req.date)
        if existing.exists():
            continue  # نادیده بگیر چون پر شده

        # بررسی محدودیت هفتگی
        week_start = req.date - timedelta(days=req.date.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_shifts = Shift.objects.filter(nurse=req.nurse, date__range=[week_start, week_end]).count()
        if weekly_shifts >= rules.max_shifts_per_week:
            continue

        # بررسی محدودیت روزانه
        daily_shifts = Shift.objects.filter(nurse=req.nurse, date=req.date).count()
        if daily_shifts >= rules.max_shifts_per_day:
            continue

        # بررسی شبانه اگر لازم باشد
        if req.shift_type == 'night' and not rules.allow_night_shifts:
            continue

        # بررسی استراحت بین شیفت‌ها
        previous_shift = Shift.objects.filter(nurse=req.nurse, date__lt=req.date).order_by('-date').first()
        if previous_shift:
            rest_days = (req.date - previous_shift.date).days
            if rest_days * 24 < rules.min_rest_hours_between_shifts:
                continue

        # در صورت عبور از همه چک‌ها:
        Shift.objects.create(nurse=req.nurse, date=req.date, shift_type=req.shift_type)
        assigned.append(req)

    messages.success(request, f"Schedule generated. {len(assigned)} requests were assigned.")
    return redirect('headnurse_dashboard')

@login_required
def dashboard_redirect(request):
    profile = NurseProfile.objects.get(user=request.user)
    if profile.is_headnurse:
        return redirect('headnurse_dashboard')
    return redirect('nurse_dashboard')

@login_required
def headnurse_dashboard(request):
    profile = NurseProfile.objects.get(user=request.user)
    if not profile.is_headnurse:
        raise PermissionDenied()
    shifts = Shift.objects.all()
    requests = ShiftRequest.objects.all()
    return render(request, 'schedule/headnurse_dashboard.html', {
        'shifts': shifts,
        'requests': requests,
    })

@login_required
def nurse_dashboard(request):
    profile = NurseProfile.objects.get(user=request.user)
    shift_requests = ShiftRequest.objects.filter(nurse=profile)
    return render(request, 'schedule/nurse_dashboard.html', {
        'nurse': profile,
        'shift_requests': shift_requests
    })