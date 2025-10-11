import logging
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import InventoryItem, InventoryMovement
from .forms import InventoryItemForm

logger = logging.getLogger(__name__)


# ======================================
# 🔹 LISTADO PRINCIPAL DE INSUMOS
# ======================================
class InventoryListView(LoginRequiredMixin, ListView):
    """Vista principal del inventario (insumos activos con estado visual)."""
    model = InventoryItem
    template_name = "inventory/list.html"
    context_object_name = "items"
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = InventoryItem.objects.filter(is_active=True)
        if q:
            qs = qs.filter(name__icontains=q)
        logger.debug(f"[INVENTORY] Listando insumos → búsqueda='{q}'")
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = InventoryItemForm()
        ctx["query"] = self.request.GET.get("q", "")

        # 🧭 Estado visual del stock con control Decimal
        for item in ctx["items"]:
            if item.min_stock == 0:
                item.stock_status = "Normal"
                continue

            ratio = item.current_stock / item.min_stock

            if item.current_stock <= item.min_stock:
                item.stock_status = "Crítico"
            elif ratio <= Decimal("1.25"):
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
        logger.info(f"[INVENTORY] Insumo creado → {form.instance.name}")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Corrige los errores antes de continuar.")
        items = InventoryItem.objects.filter(is_active=True)
        logger.warning("[INVENTORY] Error al crear insumo.")
        return render(self.request, "inventory/list.html", {"items": items, "form": form})


# ======================================
# 🔹 EDITAR INSUMO (vía offcanvas)
# ======================================
class InventoryEditPartialView(LoginRequiredMixin, UpdateView):
    """Edita un insumo existente (vía offcanvas o modal)."""
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
            logger.info(f"[INVENTORY] Insumo editado → {self.object.name}")
            return JsonResponse({"success": True, "redirect": str(reverse_lazy("inventory:list"))})
        html = render_to_string(self.template_name, {"form": form}, request)
        return JsonResponse({"success": False, "html": html})


# ======================================
# 🔹 DESACTIVAR INSUMO (soft delete)
# ======================================
class InventoryDeactivateView(LoginRequiredMixin, View):
    """Desactiva un insumo sin eliminarlo físicamente."""
    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        item.is_active = False
        item.save()
        messages.warning(request, f"Insumo '{item.name}' desactivado correctamente.")
        logger.warning(f"[INVENTORY] Insumo desactivado → {item.name}")
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
        qs = InventoryMovement.objects.select_related("item", "order", "user", "related_service")
        if q:
            qs = qs.filter(item__name__icontains=q)
        logger.debug(f"[INVENTORY] Listando movimientos → búsqueda='{q}'")
        return qs
