from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Service
from .forms import ServiceForm


class ServiceListView(LoginRequiredMixin, ListView):
    """Listado principal de servicios."""
    model = Service
    template_name = "catalog/list.html"
    context_object_name = "services"
    paginate_by = 10

    def get_queryset(self):
        """Filtra servicios activos y permite búsqueda."""
        q = self.request.GET.get("q", "").strip()
        queryset = Service.objects.filter(is_active=True)
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        """Agrega formulario vacío y query actual."""
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ServiceForm()
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class ServiceCreateView(LoginRequiredMixin, CreateView):
    """Crea un nuevo servicio."""
    model = Service
    form_class = ServiceForm
    template_name = "catalog/form.html"
    success_url = reverse_lazy("catalog:list")

    def form_valid(self, form):
        """Guarda correctamente un nuevo servicio."""
        self.object = form.save()
        messages.success(self.request, "Servicio agregado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Re-renderiza el listado con errores del formulario."""
        messages.error(self.request, "Corrige los errores antes de continuar.")
        q = self.request.GET.get("q", "").strip()
        services = Service.objects.filter(is_active=True)
        if q:
            services = services.filter(name__icontains=q)
        return render(
            self.request,
            "catalog/list.html",
            {"services": services.order_by("name"), "form": form, "query": q},
        )


class ServiceEditPartialView(LoginRequiredMixin, UpdateView):
    """Edita un servicio existente (vía offcanvas o AJAX)."""
    model = Service
    form_class = ServiceForm
    template_name = "catalog/form.html"
    success_url = reverse_lazy("catalog:list")

    def get(self, request, *args, **kwargs):
        """Devuelve el formulario HTML en modo edición."""
        self.object = self.get_object()
        html = render_to_string(self.template_name, {"form": self.get_form()}, request)
        return JsonResponse({"html": html, "name": self.object.name})

    def post(self, request, *args, **kwargs):
        """Procesa la actualización vía POST (AJAX o normal)."""
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            form.save()
            messages.success(request, f"Servicio '{self.object.name}' actualizado correctamente.")
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            return redirect("catalog:list")

        html = render_to_string(self.template_name, {"form": form}, request)
        return JsonResponse({"success": False, "html": html})


class ServiceDeactivateView(LoginRequiredMixin, View):
    """Desactiva un servicio (soft delete)."""
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
        service.save()
        messages.warning(request, f"Servicio '{service.name}' desactivado correctamente.")
        return redirect("catalog:list")
