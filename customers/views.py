# customers/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q  # 👈 para búsqueda

from .models import Customer
from .forms import CustomerForm


class CustomerListView(LoginRequiredMixin, ListView):
    """Listado principal de clientes activos, con búsqueda y paginación."""
    model = Customer
    template_name = "customers/list.html"
    context_object_name = "customers"
    paginate_by = 10  # 👈 activa la paginación

    def get_queryset(self):
        """Filtra clientes activos y aplica búsqueda opcional."""
        query = self.request.GET.get("q", "").strip()
        qs = Customer.objects.filter(is_active=True)
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        """Agrega el formulario vacío y el valor de búsqueda al contexto."""
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form", CustomerForm())
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """Creación de cliente (usa el mismo formulario dentro del offcanvas)."""
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"
    success_url = reverse_lazy("customers:list")

    def form_valid(self, form):
        """Guarda y redirige tras crear un nuevo cliente."""
        self.object = form.save()
        messages.success(self.request, "Cliente agregado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        """Si hay errores, renderiza el listado con el form con errores."""
        messages.error(self.request, "Corrige los errores antes de continuar.")
        customers = Customer.objects.filter(is_active=True).order_by("name")
        return render(
            self.request,
            "customers/list.html",
            {"customers": customers, "form": form},
        )


class CustomerEditPartialView(LoginRequiredMixin, UpdateView):
    """Carga y procesa la edición de cliente vía AJAX dentro del offcanvas."""
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"
    success_url = reverse_lazy("customers:list")

    def get(self, request, *args, **kwargs):
        """Retorna el HTML del formulario precargado (modo edición)."""
        self.object = self.get_object()
        html = render_to_string(
            self.template_name,
            {"form": self.get_form()},
            request,
        )
        return JsonResponse({"html": html, "name": self.object.name})

    def post(self, request, *args, **kwargs):
        """Procesa la actualización del cliente vía POST."""
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            # Si la petición no es AJAX, redirige normalmente
            if not request.headers.get("x-requested-with") == "XMLHttpRequest":
                return redirect("customers:list")
            return JsonResponse({"success": True})

        # Si hay errores, devuelve el HTML del formulario con errores
        html = render_to_string(self.template_name, {"form": form}, request)
        return JsonResponse({"success": False, "html": html})


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de un cliente (si se necesitara más adelante)."""
    model = Customer
    template_name = "customers/view.html"
    context_object_name = "customer"


class CustomerDeactivateView(LoginRequiredMixin, View):
    """Soft delete: desactiva el cliente sin eliminarlo físicamente."""
    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        customer.is_active = False
        customer.save()
        messages.warning(request, f"Cliente '{customer.name}' desactivado correctamente.")
        return redirect("customers:list")
