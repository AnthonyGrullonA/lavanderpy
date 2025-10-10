# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Redirección raíz inteligente
def root_router(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return redirect("accounts:login")

urlpatterns = [
    # 🔹 Redirección raíz
    path("", root_router, name="root"),

    # 🔹 Autenticación y cuentas
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # 🔹 Panel principal / Dashboard
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),

    # 🔹 Clientes
    path("customers/", include(("customers.urls", "customers"), namespace="customers")),

    # 🔹 Catálogo de servicios
    path("catalog/", include(("catalog.urls", "catalog"), namespace="catalog")),

    # 🔹 Inventario de insumos
    path("inventory/", include(("inventory.urls", "inventory"), namespace="inventory")),

    # 🔹 Órdenes de servicio
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),

    # 🔹 Facturación
    path("billing/", include(("billing.urls", "billing"), namespace="billing")),

    # 🔹 Movimientos de caja
    path("cash/", include(("cash.urls", "cash"), namespace="cash")),

    # 🔹 Reportes
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),

    # 🔹 Django Admin
    path("admin/", admin.site.urls),
]
