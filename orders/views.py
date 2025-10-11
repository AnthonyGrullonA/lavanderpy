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

logger = logging.getLogger(__name__)  # Configurable desde settings.py


# ===============================
# 🔹 LISTA GENERAL DE ÓRDENES
# ===============================
class OrderListView(LoginRequiredMixin, ListView):
    """Lista principal de órdenes activas (oculta entregadas, listas y canceladas)."""
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

        logger.debug(f"[ORDERS] Filtrando órdenes → búsqueda='{q}', estado='{status}' (excluyendo {excluded})")

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
            logger.warning("[ORDERS] Intento de crear orden sin cliente seleccionado")
            messages.error(request, "Debe seleccionar un cliente antes de guardar.")
            return redirect("orders:add")

        order = Order.objects.create(
            customer_id=customer_id,
            discount=Decimal(discount_raw),
            notes=notes,
            status="pendiente",
        )
        logger.info(f"[ORDERS] Nueva orden creada → {order.code} (cliente={order.customer.name})")

        # Crear líneas
        service_ids = request.POST.getlist("service_id")
        quantities = request.POST.getlist("quantity")
        prices = request.POST.getlist("price")

        for sid, qty, price in zip(service_ids, quantities, prices):
            if sid and qty and price:
                line = OrderLine.objects.create(
                    order=order,
                    service_id=int(sid),
                    quantity=Decimal(qty),
                    unit_price=Decimal(price),
                )
                logger.debug(f"[ORDERS] + Línea agregada → {line.service.name} x{qty} (RD${price})")

        order.recalculate_totals()
        logger.info(f"[ORDERS] Totales calculados → Total={order.total_amount}, Final={order.final_amount}")

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
        logger.debug(f"[ORDERS] Cargando detalle de orden {order.code} con {order.lines.count()} líneas")
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

        # Bloquear edición de órdenes finalizadas
        if prev_status in ["entregado", "cancelado", "listo"]:
            logger.warning(f"[ORDERS] Intento de editar orden finalizada: {order.code}")
            messages.warning(self.request, "No se puede modificar una orden completada o cancelada.")
            return redirect("orders:detail", pk=order.pk)

        logger.info(f"[ORDERS] Editando orden {order.code} → {prev_status} → {new_status}")

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
# 🔹 CAMBIO RÁPIDO DE ESTADO
# ===============================
class OrderStatusUpdateView(LoginRequiredMixin, View):
    """Permite cambiar el estado directamente (botón o AJAX)."""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")

        if not new_status or new_status == order.status:
            logger.warning(f"[ORDERS] Cambio ignorado → {order.code} ya está en '{order.status}'")
            return redirect("orders:detail", pk=pk)

        if order.status in ["entregado", "cancelado", "listo"]:
            messages.warning(request, "No se puede cambiar el estado de una orden finalizada.")
            logger.warning(f"[ORDERS] Intento de modificar orden cerrada: {order.code}")
            return redirect("orders:detail", pk=pk)

        previous = order.status
        order.status = new_status
        logger.info(f"[ORDERS] {order.code} cambiando estado: {previous} → {new_status}")

        try:
            if previous != "en_proceso" and new_status == "en_proceso":
                order.consume_inventory(user=request.user)
            elif previous == "en_proceso" and new_status == "cancelado":
                order.restock_inventory(user=request.user)
        except Exception as e:
            logger.error(f"[ORDERS] Error durante cambio de estado: {e}")

        order.save(update_fields=["status"])
        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status=new_status,
            changed_by=request.user,
        )
        messages.info(request, f"Orden {order.code} actualizada a '{new_status}'.")
        return redirect("orders:detail", pk=pk)


# ===============================
# 🔹 LISTAS FILTRADAS
# ===============================
class OrderPendingListView(OrderListView):
    template_name = "orders/pending.html"

    def get_queryset(self):
        logger.debug("[ORDERS] Listando órdenes pendientes")
        return Order.objects.filter(status="pendiente").select_related("customer").prefetch_related("lines__service")


class OrderReadyListView(OrderListView):
    template_name = "orders/ready.html"

    def get_queryset(self):
        logger.debug("[ORDERS] Listando órdenes listas")
        return Order.objects.filter(status="listo").select_related("customer").prefetch_related("lines__service")


# ===============================
# 🔹 FLUJO DE ÓRDENES (KANBAN)
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
        logger.debug("[ORDERS] Renderizando vista de flujo de órdenes (Kanban)")
        return ctx


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
        logger.info(f"[ORDERS] Avanzando orden {order.code} → {next_status}")

        if not next_status:
            messages.warning(request, "No se puede avanzar más esta orden.")
            logger.warning(f"[ORDERS] No hay transición disponible para {order.code}")
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
        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status=next_status,
            changed_by=request.user,
        )
        messages.success(request, f"La orden {order.code} pasó a '{next_status}'.")
        return redirect("orders:workflow")


# ===============================
# 🔹 CANCELACIÓN DE ÓRDENES
# ===============================
class OrderCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if order.status == "cancelado":
            logger.warning(f"[ORDERS] {order.code} ya estaba cancelada")
            messages.warning(request, f"La orden {order.code} ya estaba cancelada.")
            return redirect("orders:workflow")

        previous = order.status
        order.status = "cancelado"
        logger.info(f"[ORDERS] Cancelando orden {order.code} → {previous} → cancelado")

        try:
            if previous == "en_proceso":
                order.restock_inventory(user=request.user)
        except Exception as e:
            logger.error(f"[ORDERS] Error al reponer inventario en cancelación: {e}")

        order.save(update_fields=["status"])
        OrderTracking.objects.create(
            order=order,
            previous_status=previous,
            new_status="cancelado",
            changed_by=request.user,
        )
        messages.error(request, f"Orden {order.code} cancelada correctamente.")
        return redirect("orders:workflow")
