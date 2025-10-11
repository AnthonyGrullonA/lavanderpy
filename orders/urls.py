from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("add/", views.OrderCreateView.as_view(), name="add"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.OrderEditView.as_view(), name="edit"),
    path("<int:pk>/status/", views.OrderStatusUpdateView.as_view(), name="status"),
    path("pending/", views.OrderPendingListView.as_view(), name="pending"),
    path("ready/", views.OrderReadyListView.as_view(), name="ready"),
    path("workflow/", views.OrderWorkflowView.as_view(), name="workflow"),
    path("<int:pk>/advance/", views.OrderAdvanceView.as_view(), name="advance"),
    path("<int:pk>/cancel/", views.OrderCancelView.as_view(), name="cancel"),

]
