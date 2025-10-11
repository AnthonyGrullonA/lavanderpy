# cash/urls.py
from django.urls import path
from .views import (
    CashRegisterListView, CashRegisterOpenView, CashRegisterDetailView, CloseCashRegisterView,
    CashMovementListView, CashMovementCreateView
)

app_name = "cash"

urlpatterns = [
    path("", CashRegisterListView.as_view(), name="list"),
    path("open/", CashRegisterOpenView.as_view(), name="open"),
    path("<int:pk>/", CashRegisterDetailView.as_view(), name="detail"),
    path("<int:pk>/close/", CloseCashRegisterView.as_view(), name="close"),

    path("movements/", CashMovementListView.as_view(), name="movements"),
    path("movements/new/", CashMovementCreateView.as_view(), name="movement_new"),
]
