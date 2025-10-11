from django.contrib import admin
from .models import Order, OrderLine, OrderTracking


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "customer",
        "status",
        "date_created",
        "final_amount",
        "is_paid",
        "service_summary",
    )
    list_filter = ("status", "is_paid", "date_created")
    search_fields = ("code", "customer__name")
    date_hierarchy = "date_created"
    ordering = ("-date_created",)
    list_editable = ("status", "is_paid")
    readonly_fields = ("code", "date_created")
    autocomplete_fields = ("customer",)
    fieldsets = (
        (
            "Información general",
            {
                "fields": (
                    "customer",
                    "code",
                    "status",
                    "notes",
                    "date_created",
                )
            },
        ),
        (
            "Totales y pago",
            {
                "fields": (
                    "total_amount",
                    "discount",
                    "final_amount",
                    "is_paid",
                )
            },
        ),
    )

    actions = ["marcar_en_proceso", "marcar_entregado", "cancelar_y_reponer"]

    @admin.action(description="Marcar como 'En proceso' y descontar inventario")
    def marcar_en_proceso(self, request, queryset):
        for order in queryset:
            if order.status == "pendiente":
                order.consume_inventory(user=request.user)
                order.status = "en_proceso"
                order.save()
        self.message_user(request, "Órdenes actualizadas y stock descontado correctamente.")

    @admin.action(description="Marcar como 'Entregado'")
    def marcar_entregado(self, request, queryset):
        updated = queryset.update(status="entregado")
        self.message_user(request, f"{updated} orden(es) marcadas como entregadas.")

    @admin.action(description="Cancelar orden y devolver insumos al inventario")
    def cancelar_y_reponer(self, request, queryset):
        for order in queryset:
            if order.status != "cancelado":
                order.restock_inventory(user=request.user)
                order.status = "cancelado"
                order.save()
        self.message_user(request, "Órdenes canceladas y stock devuelto al inventario.")


@admin.register(OrderLine)
class OrderLineAdmin(admin.ModelAdmin):
    list_display = ("order", "service", "quantity", "unit_price", "subtotal")
    list_filter = ("service",)
    search_fields = ("order__code", "service__name")
    autocomplete_fields = ("order", "service")
    ordering = ("-order__date_created",)


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "previous_status",
        "new_status",
        "timestamp",
        "changed_by",
        "notes",
    )
    list_filter = ("new_status", "timestamp")
    search_fields = ("order__code", "notes")
    date_hierarchy = "timestamp"
    autocomplete_fields = ("order", "changed_by")
    ordering = ("-timestamp",)
