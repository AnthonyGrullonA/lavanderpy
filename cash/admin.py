from django.contrib import admin, messages
from django.utils import timezone
from .models import CashRegister, CashMovement


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_open",
        "opened_at",
        "closed_at",
        "opened_by",
        "closed_by",
        "opening_balance",
        "closing_balance",
        "current_balance",
    )
    list_filter = ("is_open", "opened_by", "closed_by")
    search_fields = ("name",)
    ordering = ("-opened_at",)
    actions = ["cerrar_caja"]

    @admin.display(description="Balance actual (RD$)")
    def current_balance(self, obj):
        """Muestra el balance actual calculado."""
        return f"{obj.balance_actual:.2f}"

    @admin.action(description="Cerrar caja seleccionada")
    def cerrar_caja(self, request, queryset):
        """Permite cerrar manualmente una o varias cajas abiertas."""
        cerradas = 0
        for caja in queryset:
            if caja.is_open:
                caja.close(user=request.user)
                cerradas += 1
        if cerradas:
            self.message_user(
                request,
                f"{cerradas} caja(s) cerrada(s) correctamente.",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No hay cajas abiertas para cerrar.",
                messages.WARNING,
            )

    def has_add_permission(self, request):
        """
        Evita abrir más de una caja activa.
        """
        if CashRegister.objects.filter(is_open=True).exists():
            self.message_user(
                request,
                "Ya existe una caja abierta. Debe cerrarse antes de abrir una nueva.",
                messages.WARNING,
            )
            return False
        return True


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = (
        "register",
        "movement_type",
        "amount",
        "description",
        "created_at",
        "created_by",
        "related_order_display",
    )
    list_filter = ("movement_type", "register", "created_by")
    search_fields = ("description", "related_order__code")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @admin.display(description="Orden relacionada")
    def related_order_display(self, obj):
        """Evita errores si no hay orden asociada."""
        return obj.related_order.code if obj.related_order else "—"
