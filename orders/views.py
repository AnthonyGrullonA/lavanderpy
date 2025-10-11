import logging
from decimal import Decimal
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View, TemplateView

from .models import Order, OrderLine, OrderTracking
from catalog.models import Service
from customers.models import Customer
from cash.models import CashMovement, CashRegister  # ✅ integración caja

logger = logging.getLogger(__name__)


# ===============================
# 🔹 LISTA GENERAL DE ÓRDENES
# ===============================
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        excluded = ["entregado", "listo", "cancelado"]

        qs = (
            Order.objects.exclude(status__in=excluded)
            .select_related("customer")
            .prefetch_related("lines__service")
        )

        logger.debug(f"[ORDERS] Filtrando órdenes → búsqueda='{q}', estado='{status}'")

        if q:
            qs = qs.filter(Q(customer__name__icontains=q) | Q(code__icontains=q))
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-date_created")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        return ctx


# ===============================
# 🔹 CREACIÓN DE ÓRDENES
# ===============================
class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = "orders/form.html"
    fields = ["customer", "discount", "notes", "status"]
    success_url = reverse_lazy("orders:add")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["customers"] = Customer.objects.filter(is_active=True)
        ctx["services"] = Service.objects.filter(is_active=True)
        ctx["line_forms"] = []
        return ctx

    def post(self, request, *args, **kwargs):
        customer_id = request.POST.get("customer")
        discount_raw = request.POST.get("discount") or "0"
        notes = request.POST.get("notes", "")

        if not customer_id:
            messages.error(request, "Debe seleccionar un cliente antes de guardar.")
            return redirect("orders:add")

        order = Order.objects.create(
            customer_id=customer_id,
            discount=Decimal(discount_raw),
            notes=notes,
            status="pendiente",
        )

        service_ids = request.POST.getlist("service_id")
        quantities = request.POST.getlist("quantity")
        prices = request.POST.getlist("price")

        for sid, qty, price in zip(service_ids, quantities, prices):
            if sid and qty and price:
                OrderLine.objects.create(
                    order=order,
                    service_id=int(sid),
                    quantity=Decimal(qty),
                    unit_price=Decimal(price),
                )

        order.recalculate_totals()
        messages.success(request, f"Orden {order.code} creada correctamente.")
        return redirect("orders:detail", pk=order.pk)


# ===============================
# 🔹 DETALLE DE ÓRDENES
# ===============================
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = self.object
        ctx["lines"] = order.lines.select_related("service")
        ctx["tracking"] = order.tracking.all().order_by("-timestamp")

        ctx["components"] = [
            {
                "service": line.service.name,
                "components": [
                    {
                        "item": c.item.name,
                        "used": float(line.quantity * c.quantity_used),
                        "unit": getattr(c.item.unit, "name", ""),
                    }
                    for c in line.service.components.select_related("item")
                ],
            }
            for line in order.lines.all()
        ]
        return ctx


# ===============================
# 🔹 EDICIÓN DE ÓRDENES
# ===============================
class OrderEditView(LoginRequiredMixin, UpdateView):
    model = Order
    fields = ["discount", "notes", "status"]
    template_name = "orders/form.html"
    success_url = reverse_lazy("orders:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["customers"] = Customer.objects.filter(is_active=True)
        ctx["services"] = Service.objects.filter(is_active=True)
        ctx["line_forms"] = [
            SimpleNamespace(
                id=line.id,
                service_id=line.service.id,
                service_name=line.service.name,
                quantity=str(line.quantity),
                unit_price=str(line.unit_price),
                subtotal=str(line.subtotal),
            )
            for line in self.object.lines.select_related("service").all()
        ]
        return ctx

    def form_valid(self, form):
        order = form.save(commit=False)
        prev_status = Order.objects.get(pk=order.pk).status
        new_status = form.cleaned_data["status"]

        if prev_status in ["entregado", "cancelado", "listo"]:
            messages.warning(self.request, "No se puede modificar una orden completada o cancelada.")
            return redirect("orders:detail", pk=order.pk)

        try:
            if prev_status != "en_proceso" and new_status == "en_proceso":
                order.consume_inventory(user=self.request.user)
            elif prev_status == "en_proceso" and new_status == "cancelado":
                order.restock_inventory(user=self.request.user)
        except Exception as e:
            logger.error(f"[ORDERS] Error al ajustar inventario: {e}")

        order.save()
        messages.success(self.request, f"Orden {order.code} actualizada correctamente.")
        return redirect("orders:detail", pk=order.pk)


# ===============================
# 🔹 CAMBIO MANUAL DE ESTADO
# ===============================
class OrderStatusUpdateView(LoginRequiredMixin, View):
    """Permite cambiar el estado manualmente (solo uso administrativo)."""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")

        if not new_status or new_status == order.status:
            messages.warning(request, f"La orden {order.code} ya está en '{order.status}'.")
            return redirect("orders:detail", pk=pk)

        if order.status in ["entregado", "cancelado"]:
            messages.warning(request, "No se puede cambiar el estado de una orden finalizada.")
            return redirect("orders:detail", pk=pk)

        previous = order.status
        order.status = new_status
        order.save(update_fields=["status"])

        # ✅ Movimiento en caja si pasa a entregado
        if new_status == "entregado":
            active_register = CashRegister.objects.filter(is_open=True).last()
            if active_register:
                CashMovement.objects.create(
                    register=active_register,
                    movement_type="ingreso",
                    amount=order.final_amount,
                    description=f"Pago de orden {order.code}",
                    related_order=order,
                    created_by=request.user,
                )
                logger.info(f"[CASH] Movimiento registrado por entrega de {order.code}")

        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status=new_status,
            changed_by=request.user,
        )

        messages.success(request, f"Orden {order.code} actualizada a '{new_status}'.")
        return redirect("orders:detail", pk=pk)


# ===============================
# 🔹 AVANCE AUTOMÁTICO DE ESTADO
# ===============================
class OrderAdvanceView(LoginRequiredMixin, View):
    transitions = {
        "pendiente": "en_proceso",
        "en_proceso": "listo",
        "listo": "entregado",
    }

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        next_status = self.transitions.get(order.status)

        if not next_status:
            messages.warning(request, "No se puede avanzar más esta orden.")
            return redirect("orders:workflow")

        previous = order.status
        order.status = next_status

        try:
            if previous != "en_proceso" and next_status == "en_proceso":
                order.consume_inventory(user=request.user)
            elif previous == "en_proceso" and next_status == "cancelado":
                order.restock_inventory(user=request.user)
        except Exception as e:
            logger.error(f"[ORDERS] Error durante avance de estado: {e}")

        order.save(update_fields=["status"])

        # ✅ Movimiento en caja cuando pasa a entregado
        if next_status == "entregado":
            active_register = CashRegister.objects.filter(is_open=True).last()
            if active_register:
                CashMovement.objects.create(
                    register=active_register,
                    movement_type="ingreso",
                    amount=order.final_amount,
                    description=f"Pago de orden {order.code}",
                    related_order=order,
                    created_by=request.user,
                )
                logger.info(f"[CASH] Movimiento registrado por entrega de {order.code}")

        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status=next_status,
            changed_by=request.user,
        )

        messages.success(request, f"La orden {order.code} pasó a '{next_status}'.")
        return redirect("orders:workflow")


# ===============================
# 🔹 LISTAS FILTRADAS (pendientes / listas)
# ===============================
class OrderPendingListView(OrderListView):
    """Órdenes pendientes de recepción."""
    template_name = "orders/pending.html"

    def get_queryset(self):
        logger.debug("[ORDERS] Listando órdenes pendientes")
        return (
            Order.objects.filter(status="pendiente")
            .select_related("customer")
            .prefetch_related("lines__service")
        )


class OrderReadyListView(OrderListView):
    """Órdenes listas para entrega."""
    template_name = "orders/ready.html"

    def get_queryset(self):
        logger.debug("[ORDERS] Listando órdenes listas para entrega")
        return (
            Order.objects.filter(status="listo")
            .select_related("customer")
            .prefetch_related("lines__service")
        )


# ===============================
# 🔹 FLUJO DE ÓRDENES (Kanban)
# ===============================
class OrderWorkflowView(LoginRequiredMixin, TemplateView):
    template_name = "orders/workflow.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pending_orders"] = Order.objects.filter(status="pendiente").select_related("customer")
        ctx["in_process_orders"] = Order.objects.filter(status="en_proceso").select_related("customer")
        ctx["ready_orders"] = Order.objects.filter(status="listo").select_related("customer")
        ctx["delivered_orders"] = Order.objects.filter(status="entregado").select_related("customer")
        ctx["cancelled_orders"] = Order.objects.filter(status="cancelado").select_related("customer")
        logger.debug("[ORDERS] Renderizando vista Kanban de flujo de órdenes")
        return ctx


# ===============================
# 🔹 CANCELACIÓN DE ÓRDENES
# ===============================
class OrderCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if order.status == "cancelado":
            messages.warning(request, f"La orden {order.code} ya estaba cancelada.")
            return redirect("orders:workflow")

        previous = order.status
        order.status = "cancelado"

        try:
            if previous == "en_proceso":
                order.restock_inventory(user=request.user)
        except Exception as e:
            logger.error(f"[ORDERS] Error al reponer inventario: {e}")

        order.save(update_fields=["status"])
        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status="cancelado",
            changed_by=request.user,
        )
        messages.error(request, f"Orden {order.code} cancelada correctamente.")
        return redirect("orders:workflow")
