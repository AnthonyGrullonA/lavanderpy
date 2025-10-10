# catalog/urls.py
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ServiceListView.as_view(), name="list"),
    path("add/", views.ServiceCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.ServiceEditPartialView.as_view(), name="edit"),
    path("<int:pk>/deactivate/", views.ServiceDeactivateView.as_view(), name="deactivate"),  
]
