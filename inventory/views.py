from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import InventoryItem
from .forms import InventoryItemForm


class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/list.html"
    context_object_name = "items"
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        queryset = InventoryItem.objects.filter(is_active=True)
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = InventoryItemForm()
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class InventoryCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:list")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Insumo agregado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Corrige los errores antes de continuar.")
        items = InventoryItem.objects.filter(is_active=True)
        return render(self.request, "inventory/list.html", {"items": items, "form": form})


class InventoryEditPartialView(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/form.html"
    success_url = reverse_lazy("inventory:list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        html = render_to_string(self.template_name, {"form": self.get_form()}, request)
        return JsonResponse({"html": html, "name": self.object.name})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        html = render_to_string(self.template_name, {"form": form}, request)
        return JsonResponse({"success": False, "html": html})


class InventoryDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(InventoryItem, pk=pk)
        item.is_active = False
        item.save()
        messages.warning(request, f"Insumo '{item.name}' desactivado correctamente.")
        return redirect("inventory:list")
