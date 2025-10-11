from django.db import models
from django.utils import timezone
from catalog.models import Service


class Unit(models.Model):
    """Unidades de medida (ml, kg, unidad, etc.)."""
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class InventoryItem(models.Model):
    """Insumos del inventario (detergente, fundas, etiquetas, etc.)."""
    name = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_restock_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit.abbreviation})"

    @property
    def is_below_minimum(self):
        return self.current_stock < self.min_stock


class InventoryMovement(models.Model):
    """Historial de movimientos de inventario (entradas, salidas, devoluciones, ajustes)."""

    MOVEMENT_TYPES = [
        ("entrada", "Entrada manual"),
        ("salida", "Consumo por orden"),
        ("devolucion", "Devolución por cancelación"),
        ("ajuste", "Ajuste manual"),
    ]

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name="Insumo"
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements",
        verbose_name="Orden relacionada"
    )
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Servicio asociado"
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    balance_after = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Registrado por"
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.movement_type}] {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        """Actualiza automáticamente el stock del insumo."""
        if self.movement_type == "entrada":
            self.item.current_stock += self.quantity
        elif self.movement_type in ["salida", "devolucion", "ajuste"]:
            self.item.current_stock -= self.quantity

        # Guardamos el balance después del movimiento
        self.balance_after = self.item.current_stock
        self.item.last_restock_date = timezone.now().date()
        self.item.save()
        super().save(*args, **kwargs)
