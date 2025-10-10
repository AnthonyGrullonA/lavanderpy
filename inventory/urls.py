from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.InventoryListView.as_view(), name="list"),
    path("add/", views.InventoryCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.InventoryEditPartialView.as_view(), name="edit"),
    path("<int:pk>/deactivate/", views.InventoryDeactivateView.as_view(), name="deactivate"),
]
