from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomSignupView, nurse_dashboard, headnurse_dashboard, edit_profile, submit_shift_request, shift_calendar, shift_detail, register_nurse

urlpatterns = [
    path('', nurse_dashboard, name='home'),

    path("register/", views.register, name="register"),
    path("register/nurse/", register_nurse, name="register_nurse"), # head nurse controlled

    path("nurse_dashboard/", nurse_dashboard, name="nurse_dashboard"),
    path("headnurse_dashboard/", headnurse_dashboard, name="headnurse_dashboard"),

    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="account/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),
    

    path("edit_profile/",  edit_profile, name="edit_profile"),
    path("submit_shift_request/",  submit_shift_request, name="submit_shift_request"),
    path("shift_calendar/",  shift_calendar, name="shift_calendar"),
    path("shift_detail/<int:shift_id>",  shift_detail, name="shift_detail"),

]