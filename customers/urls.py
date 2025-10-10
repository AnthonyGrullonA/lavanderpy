# customers/urls.py
from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="list"),
    path("add/", views.CustomerCreateView.as_view(), name="add"),
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.CustomerEditPartialView.as_view(), name="edit"),
    path("<int:pk>/deactivate/", views.CustomerDeactivateView.as_view(), name="deactivate"),
]
