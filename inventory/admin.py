from django.contrib import admin
from .models import UnitOfMeasure, InventoryItem, StockMovement


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "current_stock", "min_stock", "is_active", "is_below_min")
    list_filter = ("unit", "is_active")
    search_fields = ("name",)
    readonly_fields = ("is_below_min",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "date")
    list_filter = ("movement_type", "date")
    search_fields = ("item__name",)
