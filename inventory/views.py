from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import InventoryItem, InventoryMovement
from .forms import InventoryItemForm


# ======================================
# 🔹 LISTADO PRINCIPAL DE INSUMOS
# ======================================
class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/list.html"
    context_object_name = "items"
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = InventoryItem.objects.filter(is_active=True)
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = InventoryItemForm()
        ctx["query"] = self.request.GET.get("q", "")

        # 🧭 Estado visual de stock
        for item in ctx["items"]:
            if item.min_stock == 0:
                item.stock_status = "Normal"
                continue

            ratio = item.current_stock / item.min_stock

            if item.current_stock <= item.min_stock:
                item.stock_status = "Crítico"
            elif ratio <= 1.25:
                item.stock_status = "Bajo"
            else:
                item.stock_status = "Normal"

        return ctx


# ======================================
# 🔹 CREAR INSUMO
# ======================================
class InventoryCreateView(LoginRequiredMixin, CreateView):
    """Crea un nuevo insumo."""
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:list")

    def form_valid(self, form):
        form.instance.is_active = True
        form.save()
        messages.success(self.request, "Insumo agregado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Corrige los errores antes de continuar.")
        items = InventoryItem.objects.filter(is_active=True)
        return render(self.request, "inventory/list.html", {"items": items, "form": form})


# ======================================
# 🔹 EDITAR INSUMO (via offcanvas)
# ======================================
class InventoryEditPartialView(LoginRequiredMixin, UpdateView):
    """Edita un insumo existente (vía offcanvas)."""
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        html = render_to_string(self.template_name, {"form": self.get_form()}, request)
        return JsonResponse({"html": html, "name": self.object.name})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, "Insumo actualizado correctamente.")
            return JsonResponse({"success": True, "redirect": str(reverse_lazy("inventory:list"))})
        html = render_to_string(self.template_name, {"form": form}, request)
        return JsonResponse({"success": False, "html": html})


# ======================================
# 🔹 DESACTIVAR INSUMO (soft delete)
# ======================================
class InventoryDeactivateView(LoginRequiredMixin, View):
    """Soft delete (desactivar insumo)."""
    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        item.is_active = False
        item.save()
        messages.warning(request, f"Insumo '{item.name}' desactivado correctamente.")
        return redirect("inventory:list")


# ======================================
# 🔹 HISTORIAL DE MOVIMIENTOS
# ======================================
class InventoryMovementListView(LoginRequiredMixin, ListView):
    """Historial completo de movimientos de inventario."""
    model = InventoryMovement
    template_name = "inventory/movements.html"
    context_object_name = "movements"
    paginate_by = 20
    ordering = ["-created_at"]

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = InventoryMovement.objects.select_related("item", "order", "user")
        if q:
            qs = qs.filter(item__name__icontains=q)
        return qs
