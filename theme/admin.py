from django.contrib import admin
from django.utils.html import format_html
from .models import Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "preview_logo", "preview_favicon", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "footer_text")
    readonly_fields = ("created_at", "updated_at", "preview_logo", "preview_favicon")

    fieldsets = (
        ("Identidad", {
            "fields": ("name", "tagline", "preloader_text", "footer_text"),
        }),
        ("Imágenes", {
            "fields": ("logo", "preview_logo", "favicon", "preview_favicon"),
        }),
        ("Estado", {
            "fields": ("is_active",),
        }),
        ("Metadatos", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # 🔹 Vista previa del logo
    def preview_logo(self, obj):
        if obj.logo:
            return format_html(
                f'<img src="{obj.logo.url}" height="60" style="border-radius:6px; background:#fff; padding:4px; border:1px solid #eee;">'
            )
        return format_html('<span style="color:#999;">Sin logo</span>')
    preview_logo.short_description = "Vista previa del logo"

    # 🔹 Vista previa del favicon
    def preview_favicon(self, obj):
        if obj.favicon:
            return format_html(
                f'<img src="{obj.favicon.url}" height="32" width="32" style="border-radius:4px; background:#fff; padding:2px; border:1px solid #eee;">'
            )
        return format_html('<span style="color:#999;">Sin favicon</span>')
    preview_favicon.short_description = "Vista previa del favicon"

    def has_add_permission(self, request):
        """Permite crear varios temas, aunque solo uno pueda estar activo."""
        return True
