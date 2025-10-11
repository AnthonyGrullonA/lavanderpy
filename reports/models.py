# reports/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SavedReport(models.Model):
    """Permite guardar configuraciones de reportes frecuentes."""
    REPORT_TYPES = [
        ("orders", "Órdenes y Ventas"),
        ("inventory", "Inventario"),
        ("cash", "Finanzas"),
        ("customers", "Clientes"),
        ("services", "Servicios"),
    ]

    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    filters = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reporte guardado"
        verbose_name_plural = "Reportes guardados"

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
