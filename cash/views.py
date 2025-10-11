import logging
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, View
from django.utils import timezone
from django.db.models import Sum

from .models import CashRegister, CashMovement

logger = logging.getLogger(__name__)


# ===============================
# 🔹 LISTADO DE CAJAS
# ===============================
class CashRegisterListView(LoginRequiredMixin, ListView):
    model = CashRegister
    template_name = "cash/list.html"
    context_object_name = "registers"

    def get_queryset(self):
        qs = CashRegister.objects.order_by("-opened_at")
        logger.debug(f"[CASH] Listando cajas ({qs.count()})")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_register"] = CashRegister.objects.filter(is_open=True).last()
        return ctx


# ===============================
# 🔹 ABRIR CAJA
# ===============================
class CashRegisterOpenView(LoginRequiredMixin, View):
    """
    Crea una nueva caja. Evita abrir si ya existe una activa.
    """
    def post(self, request):
        name = request.POST.get("name") or timezone.now().strftime("Turno %Y-%m-%d %H:%M")
        opening_balance_raw = request.POST.get("opening_balance") or "0"

        if CashRegister.objects.filter(is_open=True).exists():
            messages.warning(request, "Ya hay una caja abierta. Debe cerrarla antes de abrir otra.")
            return redirect("cash:list")

        register = CashRegister.objects.create(
            name=name,
            opened_by=request.user,
            opening_balance=Decimal(opening_balance_raw),
            is_open=True,
        )
        messages.success(request, f"Caja '{register.name}' abierta con RD$ {register.opening_balance:.2f}.")
        logger.info(f"[CASH] Caja abierta → {register.name} (saldo inicial RD$ {register.opening_balance:.2f})")
        return redirect("cash:list")


# ===============================
# 🔹 DETALLE DE CAJA
# ===============================
class CashRegisterDetailView(LoginRequiredMixin, DetailView):
    model = CashRegister
    template_name = "cash/detail.html"
    context_object_name = "register"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        register = self.object
        movements = register.movements.select_related("related_order", "created_by")

        total_ingresos = movements.filter(movement_type="ingreso").aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
        total_egresos = movements.filter(movement_type="egreso").aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        ctx.update({
            "movements": movements,
            "total_ingresos": total_ingresos,
            "total_egresos": total_egresos,
            "balance": register.opening_balance + total_ingresos - total_egresos,
        })
        logger.debug(f"[CASH] Detalle caja '{register.name}' → ingresos={total_ingresos} egresos={total_egresos}")
        return ctx


# ===============================
# 🔹 CERRAR CAJA
# ===============================
class CloseCashRegisterView(LoginRequiredMixin, View):
    def post(self, request, pk):
        register = get_object_or_404(CashRegister, pk=pk, is_open=True)
        register.close(user=request.user)
        messages.success(request, f"Caja '{register.name}' cerrada correctamente. Balance final: RD$ {register.closing_balance:.2f}")
        return redirect("cash:list")


# ===============================
# 🔹 LISTADO DE MOVIMIENTOS
# ===============================
class CashMovementListView(LoginRequiredMixin, ListView):
    model = CashMovement
    template_name = "cash/movements.html"
    context_object_name = "movements"

    def get_queryset(self):
        qs = CashMovement.objects.select_related("register", "related_order", "created_by").order_by("-created_at")
        logger.debug(f"[CASH] Listando movimientos ({qs.count()})")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_register"] = CashRegister.objects.filter(is_open=True).last()
        return ctx


# ===============================
# 🔹 CREAR MOVIMIENTO MANUAL
# ===============================
class CashMovementCreateView(LoginRequiredMixin, CreateView):
    model = CashMovement
    fields = ["movement_type", "amount", "description", "related_order"]
    template_name = "cash/form.html"
    success_url = reverse_lazy("cash:movements")

    def form_valid(self, form):
        active_register = CashRegister.objects.filter(is_open=True).last()
        if not active_register:
            messages.error(self.request, "No hay caja abierta actualmente.")
            logger.warning("[CASH] Intento de registrar movimiento sin caja abierta")
            return redirect("cash:list")

        form.instance.register = active_register
        form.instance.created_by = self.request.user
        self.object = form.save()

        messages.success(self.request, "Movimiento registrado correctamente.")
        logger.info(f"[CASH] Movimiento registrado → {self.object.get_movement_type_display()} RD$ {self.object.amount:.2f}")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Revisa los datos del movimiento.")
        return render(self.request, self.template_name, {"form": form})
