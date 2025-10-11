import datetime
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
from orders.models import Order
from inventory.models import InventoryItem
from cash.models import CashMovement, CashRegister
from customers.models import Customer


@login_required
def home_view(request):
    """Dashboard principal de Lavandería con métricas globales."""
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=7)

    # =============================
    # 🔹 MÉTRICAS DE ÓRDENES
    # =============================
    orders_today = Order.objects.filter(date_created__date=today).count()
    in_process = Order.objects.filter(status="en_proceso").count()
    delivered_today = Order.objects.filter(
        status="entregado", date_created__date=today
    ).count()

    # 🔹 Ingresos del día (por órdenes entregadas)
    cash_in = (
        CashMovement.objects.filter(
            movement_type="ingreso", created_at__date=today
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # =============================
    # 🔹 ÓRDENES RECIENTES
    # =============================
    recent_orders = (
        Order.objects.select_related("customer")
        .order_by("-date_created")[:5]
    )

    # =============================
    # 🔹 ALERTA DE INVENTARIO
    # =============================
    low_stock_items = InventoryItem.objects.filter(is_active=True).order_by(
        "current_stock"
    )[:5]
    low_stock_alerts = [
        {
            "name": item.name,
            "stock": item.current_stock,
            "min": item.min_stock,
            "status": (
                "danger"
                if item.current_stock <= item.min_stock
                else "warning"
                if item.current_stock <= item.min_stock * Decimal("1.25")
                else "normal"
            ),
        }
        for item in low_stock_items
    ]

    # =============================
    # 🔹 ÓRDENES POR ESTADO (últimos 7 días)
    # =============================
    orders_week = (
        Order.objects.filter(date_created__date__gte=week_start)
        .values("status")
        .annotate(count=Count("id"))
    )
    chart_data = {
        "pendiente": 0,
        "en_proceso": 0,
        "listo": 0,
        "entregado": 0,
    }
    for o in orders_week:
        chart_data[o["status"]] = o["count"]

    # =============================
    # 🔹 CLIENTES Y CAJA
    # =============================
    total_customers = Customer.objects.filter(is_active=True).count()
    active_register = CashRegister.objects.filter(is_open=True).last()
    cash_balance = (
        active_register.closing_balance
        if active_register and not active_register.is_open
        else (active_register.opening_balance if active_register else Decimal("0.00"))
    )

    # =============================
    # 🔹 CONTEXTO FINAL
    # =============================
    context = {
        "orders_today": orders_today,
        "in_process": in_process,
        "delivered_today": delivered_today,
        "cash_in": cash_in,
        "recent_orders": recent_orders,
        "low_stock_alerts": low_stock_alerts,
        "chart_data": chart_data,
        "total_customers": total_customers,
        "cash_balance": cash_balance,
    }

    return render(request, "dashboard/home.html", context)
