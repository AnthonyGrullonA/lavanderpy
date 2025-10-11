from django.contrib import admin
from .models import (
    ServiceCategory,
    Service,
    ServiceMaterial,
    ServicePricing,
    ServiceComponent,
)


# --- Inlines ---

class ServiceMaterialInline(admin.TabularInline):
    """Insumos (materiales) asociados a un servicio."""
    model = ServiceMaterial
    extra = 1
    autocomplete_fields = ["item"]
    fields = ("item", "quantity_used", "unit_of_measure")
    verbose_name = "Insumo"
    verbose_name_plural = "Insumos utilizados"


class ServiceComponentInline(admin.TabularInline):
    """Componentes técnicos o partes vinculadas a un servicio."""
    model = ServiceComponent
    extra = 1
    autocomplete_fields = ["item"]
    fields = ("item", "quantity_used")
    verbose_name = "Componente"
    verbose_name_plural = "Componentes del servicio"


class ServicePricingInline(admin.TabularInline):
    """Gestión de precios por tipo de cliente dentro del mismo servicio."""
    model = ServicePricing
    extra = 1
    fields = ("customer_type", "price")
    verbose_name = "Precio personalizado"
    verbose_name_plural = "Precios por tipo de cliente"


# --- Administración principal ---

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "unit_type",
        "base_price",
        "is_active",
        "is_express_available",
    )
    list_filter = ("category", "unit_type", "is_active", "is_express_available")
    search_fields = ("name", "description")
    list_editable = ("is_active", "is_express_available")
    inlines = [ServiceMaterialInline, ServiceComponentInline, ServicePricingInline]
    ordering = ("name",)
    fieldsets = (
        ("Información general", {
            "fields": (
                "name",
                "category",
                "description",
                "unit_type",
                "base_price",
                "estimated_time_minutes",
            )
        }),
        ("Configuración operativa", {
            "fields": (
                "is_express_available",
                "is_active",
            ),
        }),
    )


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ServiceMaterial)
class ServiceMaterialAdmin(admin.ModelAdmin):
    list_display = ("service", "item", "quantity_used", "unit_of_measure")
    list_filter = ("service__category",)
    search_fields = ("service__name", "item__name")
    autocomplete_fields = ["service", "item"]
    ordering = ("service",)


@admin.register(ServiceComponent)
class ServiceComponentAdmin(admin.ModelAdmin):
    list_display = ("service", "item", "quantity_used")
    list_filter = ("service__category",)
    search_fields = ("service__name", "item__name")
    autocomplete_fields = ["service", "item"]
    ordering = ("service",)


@admin.register(ServicePricing)
class ServicePricingAdmin(admin.ModelAdmin):
    list_display = ("service", "customer_type", "price")
    list_filter = ("customer_type",)
    search_fields = ("service__name",)
    autocomplete_fields = ["service"]
    ordering = ("service", "customer_type")
