from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_router(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return redirect("accounts:login")

urlpatterns = [
    path("", root_router, name="root"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("admin/", admin.site.urls),
]
