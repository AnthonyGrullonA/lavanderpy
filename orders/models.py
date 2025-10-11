from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from inventory.models import InventoryMovement  # 👈 integración directa con inventario


class Order(models.Model):
    """Orden principal de la lavandería (pedido del cliente)."""

    STATUS_CHOICES = [
        ("pendiente", "Pendiente de recepción"),
        ("en_proceso", "En proceso de lavado"),
        ("listo", "Listo para entrega"),
        ("entregado", "Entregado al cliente"),
        ("cancelado", "Cancelado"),
    ]

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Cliente",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Código de orden",
    )
    date_created = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendiente")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas internas")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ["-date_created"]

    def __str__(self):
        return f"#{self.code} - {self.customer.name}"

    def save(self, *args, **kwargs):
        """Genera un código único al crear una nueva orden."""
        if not self.code:
            last = Order.objects.order_by("-id").first()
            next_number = (last.id + 1) if last else 1
            self.code = f"ORD-{str(next_number).zfill(5)}"
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """Recalcula los totales basados en las líneas asociadas."""
        total = sum((line.subtotal or Decimal("0")) for line in self.lines.all())
        self.total_amount = Decimal(total)
        self.final_amount = Decimal(total) - Decimal(self.discount or 0)
        self.save(update_fields=["total_amount", "final_amount"])

    @property
    def service_summary(self):
        """Lista de servicios usados en formato compacto."""
        return ", ".join([l.service.name for l in self.lines.all()]) or "Sin servicios"

    # ==== CONTROL DE INVENTARIO CON MOVIMIENTOS ====

    @transaction.atomic
    def consume_inventory(self, user=None):
        """Descuenta insumos del inventario y registra movimiento."""
        for line in self.lines.select_related("service"):
            for component in line.service.components.select_related("item"):
                total_to_consume = Decimal(line.quantity) * component.quantity_used
                item = component.item

                # Actualizar stock
                item.current_stock = max(Decimal("0.00"), item.current_stock - total_to_consume)
                item.save(update_fields=["current_stock"])

                # Registrar movimiento
                InventoryMovement.objects.create(
                    item=item,
                    order=self,
                    movement_type="salida",
                    quantity=total_to_consume,
                    balance_after=item.current_stock,
                    user=user,
                    notes=f"Consumo de {total_to_consume} por servicio '{line.service.name}' en orden {self.code}"
                )

    @transaction.atomic
    def restock_inventory(self, user=None):
        """Devuelve insumos al inventario (por cancelación o error)."""
        for line in self.lines.select_related("service"):
            for component in line.service.components.select_related("item"):
                total_to_return = Decimal(line.quantity) * component.quantity_used
                item = component.item
                item.current_stock += total_to_return
                item.save(update_fields=["current_stock"])

                # Registrar movimiento de devolución
                InventoryMovement.objects.create(
                    item=item,
                    order=self,
                    movement_type="devolucion",
                    quantity=total_to_return,
                    balance_after=item.current_stock,
                    user=user,
                    notes=f"Devolución de {total_to_return} por cancelación de orden {self.code}"
                )


class OrderLine(models.Model):
    """Detalle de la orden: servicios seleccionados y cantidades."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Orden",
    )
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.PROTECT,
        verbose_name="Servicio",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de orden"
        verbose_name_plural = "Detalles de órdenes"

    def __str__(self):
        return f"{self.service.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        """Guarda la línea y recalcula el subtotal y los totales."""
        self.subtotal = Decimal(self.unit_price) * Decimal(self.quantity)
        super().save(*args, **kwargs)
        self.order.recalculate_totals()


class OrderTracking(models.Model):
    """Historial de estados y seguimiento de la orden."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking",
        verbose_name="Orden",
    )
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    changed_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modificado por",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historial de orden"
        verbose_name_plural = "Historial de órdenes"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.order.code} → {self.new_status}"
