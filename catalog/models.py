from django.db import models

class ServiceCategory(models.Model):
    """Agrupa servicios (ej. Lavado, Planchado, Tintorería)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de servicio"
        verbose_name_plural = "Categorías de servicios"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    """Define cada servicio ofrecido en la lavandería."""
    UNIT_CHOICES = [
        ("prenda", "Por prenda"),
        ("libra", "Por libra"),
        ("kilo", "Por kilo"),
        ("servicio", "Por servicio completo"),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES, default="prenda")

    # Precio base por unidad (se ajusta por tipo de cliente en billing)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Tiempo estimado de proceso
    estimated_time_minutes = models.PositiveIntegerField(default=30)

    # Indicadores operativos
    is_express_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()})"


class ServiceMaterial(models.Model):
    """Relación entre servicio e insumos consumidos."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="materials")
    item_name = models.CharField(max_length=100)  # luego será FK a InventoryItem
    unit_of_measure = models.CharField(max_length=20, default="ml")
    quantity_used = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        verbose_name = "Insumo de servicio"
        verbose_name_plural = "Insumos de servicio"

    def __str__(self):
        return f"{self.item_name} - {self.quantity_used} {self.unit_of_measure}"


class ServicePricing(models.Model):
    """Permite personalizar precios según tipo de cliente."""
    SERVICE_CLIENT_TYPES = [
        ("personal", "Cliente personal"),
        ("empresa", "Cliente empresarial"),
        ("vip", "Cliente VIP"),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="pricing")
    customer_type = models.CharField(max_length=20, choices=SERVICE_CLIENT_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Precio por tipo de cliente"
        verbose_name_plural = "Precios por tipo de cliente"
        unique_together = ("service", "customer_type")

    def __str__(self):
        return f"{self.service.name} - {self.customer_type}: {self.price} RD$"
