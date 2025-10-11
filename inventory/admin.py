from django.contrib import admin
from .models import Unit, InventoryItem, InventoryMovement


# ======================================================
# 🔹 ADMIN: UNIDADES DE MEDIDA
# ======================================================
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")
    ordering = ("name",)
    list_per_page = 25


# ======================================================
# 🔹 ADMIN: INSUMOS DE INVENTARIO
# ======================================================
@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "unit",
        "current_stock",
        "min_stock",
        "cost_per_unit",
        "stock_status",
        "last_restock_date",
        "is_active",
    )
    list_filter = ("unit", "is_active")
    search_fields = ("name",)
    ordering = ("name",)
    list_editable = ("current_stock", "min_stock", "cost_per_unit", "is_active")
    readonly_fields = ("last_restock_date",)
    list_per_page = 25

    def stock_status(self, obj):
        """Muestra si el insumo está por debajo del mínimo."""
        if obj.current_stock < obj.min_stock:
            return "⚠️ Bajo stock"
        return "✅ Suficiente"
    stock_status.short_description = "Estado del stock"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("unit")


# ======================================================
# 🔹 ADMIN: HISTORIAL DE MOVIMIENTOS
# ======================================================
@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    """Historial detallado de movimientos de inventario."""
    list_display = (
        "item",
        "movement_type",
        "quantity",
        "balance_after",
        "order",
        "related_service",
        "user",
        "created_at",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = ("item__name", "order__code", "notes", "related_service__name")
    readonly_fields = ("created_at", "balance_after")
    autocomplete_fields = ("item", "order", "user", "related_service")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Información del movimiento",
            {
                "fields": (
                    "movement_type",
                    "item",
                    "order",
                    "related_service",
                    "quantity",
                    "balance_after",
                    "user",
                    "notes",
                )
            },
        ),
        (
            "Registro del sistema",
            {"classes": ("collapse",), "fields": ("created_at",)},
        ),
    )

    def has_add_permission(self, request):
        """Solo usuarios staff pueden registrar movimientos manualmente."""
        return request.user.is_staff

    def save_model(self, request, obj, form, change):
        """Asigna el usuario automáticamente si no está especificado."""
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)
