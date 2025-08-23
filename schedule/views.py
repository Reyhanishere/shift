from typing import Any 
from datetime import timedelta
import json

from django.contrib import messages
from django.http import HttpResponse, HttpRequest,JsonResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView
# from django.views.generic import ( CreateView, ListView, UpdateView, DeleteView )
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms.models import BaseModelForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from allauth.account.views import SignupView as AllauthSignupView

from .forms import UserRegisterForm, NurseProfileForm, ShiftRequestForm
from .models import Shift, NurseProfile, ShiftRequest, UserProfileSchedulingRule


def home(request):
    """Public home page showing all shifts"""
    shifts = Shift.objects.all()
    return render(request, "shifts/home.html", {"shifts": shifts})


def register(request):
    """Register new users via form"""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created. You can now log in.")
            return redirect("login")
    else:
        form = UserRegisterForm()
    return render(request, "schedule/register.html", {"form": form})


@login_required
def nurse_dashboard(request):
    """Dashboard for nurses showing their shift requests"""
    profile = NurseProfile.objects.get(user=request.user)
    shift_requests = ShiftRequest.objects.filter(nurse=profile)
    return render(
        request,
        "schedule/nurse_dashboard.html",
        {"nurse": profile, "shift_requests": shift_requests},
    )


@login_required
def headnurse_dashboard(request):
    """Dashboard for head nurses with full control"""
    profile = NurseProfile.objects.get(user=request.user)
    if not profile.is_headnurse:
        raise PermissionDenied()
    shifts = Shift.objects.all()
    requests = ShiftRequest.objects.all()
    return render(
        request,
        "schedule/headnurse_dashboard.html",
        {"shifts": shifts, "requests": requests},
    )


def register_nurse(request):
    """Simple nurse registration (head nurse controlled)"""
    if request.method == "POST":
        full_name = request.POST["full_name"]
        position = request.POST["position"]
        username = request.POST["username"]
        password = request.POST["password"]

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password)
        NurseProfile.objects.create(user=user, full_name=full_name, position=position)
        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    """Custom login view"""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("nurse_dashboard")
        messages.error(request, "Invalid username or password.")
        return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    """Custom logout view"""
    logout(request)
    return redirect("login")


@login_required
def edit_profile(request):
    """Edit nurse profile"""
    profile, _ = NurseProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = NurseProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("nurse_dashboard")
    else:
        form = NurseProfileForm(instance=profile)

    return render(request, "schedule/edit_profile.html", {"form": form})


@login_required
def submit_shift_request(request):
    """Nurses submit shift change requests"""
    if request.method == "POST":
        form = ShiftRequestForm(request.POST)
        if form.is_valid():
            shift_request = form.save(commit=False)
            shift_request.nurse = request.user.nurseprofile
            shift_request.save()
            return redirect("nurse_dashboard")
    else:
        form = ShiftRequestForm()

    return render(request, "schedule/submit_shift_request.html", {"form": form})


@login_required
def view_schedule(request):
    """Show nurse their assigned shifts"""
    shifts = Shift.objects.filter(assigned_nurse=request.user).order_by("date")
    return render(request, "schedule/view_schedule.html", {"shifts": shifts})


@login_required
def shift_calendar(request):
    """Calendar view (AJAX events)"""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        shifts = Shift.objects.filter(assigned_nurse=request.user).order_by("date")
        events = [
            {"title": f"{shift.shift_type} Shift", "start": shift.date.isoformat(), "allDay": True}
            for shift in shifts
        ]
        return JsonResponse(events, safe=False)

    return render(request, "schedule/calendar.html")


def shift_detail(request, shift_id):
    """Detailed view of a shift"""
    shift = get_object_or_404(Shift, id=shift_id)
    nurses = NurseProfile.objects.all()
    return render(request, "schedule/shift_detail.html", {"shift": shift, "nurses": nurses})


def is_headnurse(user):
    return user.is_authenticated and hasattr(user, "nurseprofile") and user.nurseprofile.is_headnurse


@login_required
@user_passes_test(is_headnurse)
def generate_schedule(request):
    """Head nurse generates schedule based on rules & requests"""
    rules = UserProfileSchedulingRule.objects.first()
    if not rules:
        messages.error(request, "Scheduling rules are not set.")
        return redirect("headnurse_dashboard")

    requests = ShiftRequest.objects.all().order_by("date", "shift_type")
    assigned = []

    for req in requests:
        if Shift.objects.filter(nurse=req.nurse, date=req.date).exists():
            continue

        week_start = req.date - timedelta(days=req.date.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_shifts = Shift.objects.filter(nurse=req.nurse, date__range=[week_start, week_end]).count()
        if weekly_shifts >= rules.max_shifts_per_week:
            continue

        daily_shifts = Shift.objects.filter(nurse=req.nurse, date=req.date).count()
        if daily_shifts >= rules.max_shifts_per_day:
            continue

        if req.shift_type == "night" and not rules.allow_night_shifts:
            continue

        previous_shift = (
            Shift.objects.filter(nurse=req.nurse, date__lt=req.date).order_by("-date").first()
        )
        if previous_shift:
            rest_days = (req.date - previous_shift.date).days
            if rest_days * 24 < rules.min_rest_hours_between_shifts:
                continue

        Shift.objects.create(nurse=req.nurse, date=req.date, shift_type=req.shift_type)
        assigned.append(req)

    messages.success(request, f"Schedule generated. {len(assigned)} requests were assigned.")
    return redirect("headnurse_dashboard")


@login_required
def dashboard_redirect(request):
    """Redirect to correct dashboard depending on role"""
    profile = NurseProfile.objects.get(user=request.user)
    if profile.is_headnurse:
        return redirect("headnurse_dashboard")
    return redirect("nurse_dashboard")


# ---------------- AUTH / SIGNUP ---------------- #

class CustomSignupView(AllauthSignupView):
    """Custom Allauth signup view"""
    template_name = "account/signup.html"
    def get_success_url(self):
        return reverse_lazy("home")