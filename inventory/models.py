from django.db import models


class UnitOfMeasure(models.Model):
    """Unidades estandarizadas para medir insumos."""
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class InventoryItem(models.Model):
    """Representa un insumo físico en inventario."""
    name = models.CharField(max_length=100, unique=True)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.unit.abbreviation})"

    def is_below_min(self):
        """Devuelve True si está por debajo del mínimo."""
        return self.current_stock <= self.min_stock


class StockMovement(models.Model):
    """Registra movimientos de entrada y salida."""
    MOVEMENT_TYPES = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.movement_type.title()} - {self.item.name} ({self.quantity})"
