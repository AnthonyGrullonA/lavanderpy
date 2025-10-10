from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "customer_type", "phone", "is_active", "created_at")
    list_filter = ("customer_type", "is_active")
    search_fields = ("name", "phone", "email")
    actions = ["desactivar_clientes"]

    def desactivar_clientes(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} clientes desactivados correctamente.")
    desactivar_clientes.short_description = "Desactivar clientes seleccionados"
