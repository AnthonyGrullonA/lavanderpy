from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("orders/", views.OrdersReportView.as_view(), name="orders_report"),
    path("inventory/", views.InventoryReportView.as_view(), name="inventory_report"),
    path("financial/", views.FinancialReportView.as_view(), name="financial_report"),
    path("customers/", views.CustomersReportView.as_view(), name="customers_report"),
    path("services/", views.ServicesReportView.as_view(), name="services_report"),
]
