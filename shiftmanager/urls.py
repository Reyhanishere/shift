from django.contrib import admin
from django.urls import path, include
from schedule.views import CustomSignupView


urlpatterns = [
    path('admin/', admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("__reload__/", include("django_browser_reload.urls")),

    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    path("accounts/", include("allauth.urls")),

   
    path('', include('schedule.urls')),
]
