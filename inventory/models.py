import logging
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from catalog.models import Service

logger = logging.getLogger(__name__)
User = get_user_model()


# ======================================================
# 🔹 UNIDADES DE MEDIDA
# ======================================================
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


# ======================================================
# 🔹 INSUMOS DE INVENTARIO
# ======================================================
class InventoryItem(models.Model):
    """Insumos controlados en stock (detergentes, fundas, etiquetas...)."""
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

    # 🔹 Método auxiliar para registrar movimiento
    def record_movement(self, quantity, movement_type, user=None, related_order=None, related_service=None, notes=""):
        """Registra y aplica un movimiento de inventario."""
        from .models import InventoryMovement
        logger.info(f"[INVENTORY] Movimiento '{movement_type}' → {self.name}: {quantity}")

        movement = InventoryMovement.objects.create(
            item=self,
            quantity=Decimal(quantity),
            movement_type=movement_type,
            order=related_order,
            related_service=related_service,
            user=user,
            notes=notes,
        )

        # Ajustar stock
        if movement_type == "entrada":
            self.current_stock += Decimal(quantity)
        elif movement_type == "salida":
            self.current_stock -= Decimal(quantity)
        elif movement_type == "devolucion":
            self.current_stock += Decimal(quantity)
        elif movement_type == "ajuste":
            self.current_stock += Decimal(quantity)

        self.last_restock_date = timezone.now().date()
        self.save()

        movement.balance_after = self.current_stock
        movement.save()
        return movement


# ======================================================
# 🔹 HISTORIAL DE MOVIMIENTOS
# ======================================================
class InventoryMovement(models.Model):
    """Registro histórico de movimientos (entradas, salidas, devoluciones, ajustes)."""
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
        verbose_name="Insumo",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements",
        verbose_name="Orden relacionada",
    )
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Servicio asociado",
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    balance_after = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Registrado por",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.movement_type}] {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        """Actualiza automáticamente el stock en cada movimiento."""
        super().save(*args, **kwargs)
        logger.debug(f"[INVENTORY] Movimiento guardado: {self}")
