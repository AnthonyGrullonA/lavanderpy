from django.contrib import admin
from .models import ServiceCategory, Service, ServiceMaterial, ServicePricing


class ServiceMaterialInline(admin.TabularInline):
    """Permite agregar insumos directamente dentro del servicio."""
    model = ServiceMaterial
    extra = 1
    fields = ("item_name", "unit_of_measure", "quantity_used")
    verbose_name = "Insumo"
    verbose_name_plural = "Insumos del servicio"


class ServicePricingInline(admin.TabularInline):
    """Permite definir precios personalizados dentro del servicio."""
    model = ServicePricing
    extra = 1
    fields = ("customer_type", "price")
    verbose_name = "Precio por tipo de cliente"
    verbose_name_plural = "Precios personalizados"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin principal del servicio."""
    list_display = ("name", "category", "unit_type", "base_price", "is_active")
    list_filter = ("category", "unit_type", "is_active")
    search_fields = ("name", "description")
    ordering = ("name",)
    inlines = [ServiceMaterialInline, ServicePricingInline]

    fieldsets = (
        ("Información general", {
            "fields": ("name", "category", "description", "unit_type", "base_price", "estimated_time_minutes")
        }),
        ("Configuraciones adicionales", {
            "fields": ("is_express_available", "is_active"),
        }),
    )


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Admin de categorías de servicios."""
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ServiceMaterial)
class ServiceMaterialAdmin(admin.ModelAdmin):
    """Admin independiente para insumos."""
    list_display = ("service", "item_name", "quantity_used", "unit_of_measure")
    list_filter = ("unit_of_measure",)
    search_fields = ("item_name", "service__name")


@admin.register(ServicePricing)
class ServicePricingAdmin(admin.ModelAdmin):
    """Admin de precios personalizados por tipo de cliente."""
    list_display = ("service", "customer_type", "price")
    list_filter = ("customer_type",)
    search_fields = ("service__name",)
    ordering = ("service__name",)
