from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register_nurse, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='schedule/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='schedule/logout.html'), name='logout'),
    
    path('nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('headnurse/', views.headnurse_dashboard, name='headnurse_dashboard'),


    path('', views.home, name='home'),

    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('shift-request/', views.submit_shift_request, name='submit_shift_request'),
    path('my-schedule/', views.view_schedule, name='view_schedule'),

    path('calendar/', views.shift_calendar, name='shift_calendar'),
    path('shift/<int:shift_id>/', views.shift_detail, name='shift_detail'),

    path('generate-schedule/', views.generate_schedule, name='generate_schedule'),

    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('headnurse/', views.headnurse_dashboard, name='headnurse_dashboard'),


]
