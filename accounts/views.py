from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy

from .forms import LoginForm, ProfileForm, RegisterForm


def root_view(request):
    """
    Vista raíz: enruta según autenticación.
    - Autenticado -> dashboard:home
    - Anónimo     -> accounts:login
    """
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return redirect("accounts:login")


def login_view(request):
    """
    Login:
    - Si ya está autenticado -> dashboard
    - POST válido -> login + redirect a ?next= o dashboard
    """
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or reverse("dashboard:home")
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """Cierra sesión y vuelve al login."""
    if request.user.is_authenticated:
        messages.info(request, "Sesión cerrada correctamente.")
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    """Perfil del usuario autenticado."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})

@login_required

def register_view(request):
    """
    Registro:
    - Si autenticado -> dashboard (no tiene sentido registrarse de nuevo)
    - POST válido -> crea usuario, inicia sesión y va al dashboard
    """
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            messages.success(request, "Registro exitoso. ¡Bienvenido!")
            return redirect("dashboard:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


# ===== Cambio de contraseña (opcional recomendado) =====

class PasswordChangeViewCustom(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class PasswordChangeDoneViewCustom(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"
