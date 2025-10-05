# accounts/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("register/", views.register_view, name="register"),

    # Opcional recomendado (usa vistas customizadas basadas en built-in)
    path("password-change/", views.PasswordChangeViewCustom.as_view(), name="password_change"),
    path("password-change/done/", views.PasswordChangeDoneViewCustom.as_view(), name="password_change_done"),
]
