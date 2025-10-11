# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

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

    # 🔹 Movimientos de caja
    path("cash/", include(("cash.urls", "cash"), namespace="cash")),

    # 🔹 Reportes
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),

    # 🔹 Django Admin
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)