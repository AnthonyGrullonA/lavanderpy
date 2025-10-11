import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, Q
from django.views.generic import TemplateView

from orders.models import Order, OrderLine
from customers.models import Customer
from catalog.models import Service, ServiceCategory
from inventory.models import InventoryItem, InventoryMovement
from cash.models import CashRegister, CashMovement

logger = logging.getLogger(__name__)


# =====================================================
# 🔹 BASE VIEW
# =====================================================
class BaseReportView(LoginRequiredMixin, TemplateView):
    """Base para todos los reportes: agrega soporte de filtros globales."""

    def get_date_range(self):
        """Devuelve rango de fechas válido desde GET params."""
        try:
            start = datetime.strptime(self.request.GET.get("start", ""), "%Y-%m-%d").date()
        except Exception:
            start = None
        try:
            end = datetime.strptime(self.request.GET.get("end", ""), "%Y-%m-%d").date()
        except Exception:
            end = None
        return start, end


# =====================================================
# 📊 1️⃣ REPORTES DE ÓRDENES Y VENTAS
# =====================================================
class OrdersReportView(BaseReportView):
    template_name = "reports/orders.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = self.get_date_range()

        qs = Order.objects.all().select_related("customer")
        if start:
            qs = qs.filter(date_created__date__gte=start)
        if end:
            qs = qs.filter(date_created__date__lte=end)

        total_orders = qs.count()
        total_sales = qs.aggregate(total=Sum("final_amount"))["total"] or Decimal("0.00")
        avg_ticket = (total_sales / total_orders) if total_orders else Decimal("0.00")

        top_services = (
            OrderLine.objects.values(name=F("service__name"))
            .annotate(total=Sum("subtotal"), qty=Sum("quantity"))
            .order_by("-total")[:5]
        )

        top_customers = (
            qs.values(name=F("customer__name"))
            .annotate(total=Sum("final_amount"), count=Count("id"))
            .order_by("-total")[:5]
        )

        ctx.update({
            "start": start,
            "end": end,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "avg_ticket": avg_ticket,
            "top_services": top_services,
            "top_customers": top_customers,
            "orders": qs.order_by("-date_created")[:50],
        })
        logger.debug(f"[REPORT] OrdersReport → {total_orders} órdenes, RD${total_sales}")
        return ctx


# =====================================================
# 📦 2️⃣ REPORTES DE INVENTARIO
# =====================================================
class InventoryReportView(BaseReportView):
    template_name = "reports/inventory.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = self.get_date_range()

        items = InventoryItem.objects.all()
        if start or end:
            moves = InventoryMovement.objects.all()
            if start:
                moves = moves.filter(created_at__date__gte=start)
            if end:
                moves = moves.filter(created_at__date__lte=end)
        else:
            moves = InventoryMovement.objects.all()

        total_entries = moves.filter(movement_type="entrada").aggregate(Sum("quantity"))["quantity__sum"] or 0
        total_exits = moves.filter(movement_type="salida").aggregate(Sum("quantity"))["quantity__sum"] or 0

        low_stock = items.filter(current_stock__lte=F("min_stock")).count()
        critical_stock = items.filter(current_stock__lt=F("min_stock") / 2).count()

        ctx.update({
            "start": start,
            "end": end,
            "items": items.order_by("name"),
            "movements": moves.order_by("-created_at")[:50],
            "total_entries": total_entries,
            "total_exits": total_exits,
            "low_stock": low_stock,
            "critical_stock": critical_stock,
        })
        logger.debug(f"[REPORT] InventoryReport → Entradas={total_entries}, Salidas={total_exits}")
        return ctx


# =====================================================
# 💰 3️⃣ REPORTES FINANCIEROS
# =====================================================
class FinancialReportView(BaseReportView):
    template_name = "reports/financial.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = self.get_date_range()

        movements = CashMovement.objects.all()
        if start:
            movements = movements.filter(created_at__date__gte=start)
        if end:
            movements = movements.filter(created_at__date__lte=end)

        total_ingresos = movements.filter(movement_type="ingreso").aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
        total_egresos = movements.filter(movement_type="egreso").aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
        balance = total_ingresos - total_egresos

        registers = CashRegister.objects.order_by("-opened_at")[:5]

        ctx.update({
            "start": start,
            "end": end,
            "movements": movements.order_by("-created_at")[:50],
            "total_ingresos": total_ingresos,
            "total_egresos": total_egresos,
            "balance": balance,
            "registers": registers,
        })
        logger.debug(f"[REPORT] FinancialReport → Ingresos={total_ingresos}, Egresos={total_egresos}")
        return ctx


# =====================================================
# 👥 4️⃣ REPORTES DE CLIENTES
# =====================================================
class CustomersReportView(BaseReportView):
    template_name = "reports/customers.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = self.get_date_range()

        orders = Order.objects.all().select_related("customer")
        if start:
            orders = orders.filter(date_created__date__gte=start)
        if end:
            orders = orders.filter(date_created__date__lte=end)

        customer_stats = (
            orders.values("customer__name", "customer__customer_type")
            .annotate(total=Sum("final_amount"), count=Count("id"))
            .order_by("-total")[:20]
        )

        ctx.update({
            "start": start,
            "end": end,
            "customer_stats": customer_stats,
        })
        logger.debug(f"[REPORT] CustomersReport → {len(customer_stats)} clientes")
        return ctx


# =====================================================
# 🧾 5️⃣ REPORTES DE SERVICIOS
# =====================================================
class ServicesReportView(BaseReportView):
    template_name = "reports/services.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = self.get_date_range()

        lines = OrderLine.objects.select_related("service", "order")
        if start:
            lines = lines.filter(order__date_created__date__gte=start)
        if end:
            lines = lines.filter(order__date_created__date__lte=end)

        service_stats = (
            lines.values("service__name", "service__category__name")
            .annotate(total_sales=Sum("subtotal"), total_qty=Sum("quantity"))
            .order_by("-total_sales")[:20]
        )

        # ✅ Ajuste aquí: ahora usa "services" (por el related_name en catalog.models)
        categories = (
            ServiceCategory.objects.annotate(service_count=Count("services"))
            .order_by("name")
        )

        ctx.update({
            "start": start,
            "end": end,
            "service_stats": service_stats,
            "categories": categories,
        })
        logger.debug(f"[REPORT] ServicesReport → {len(service_stats)} servicios analizados")
        return ctx
