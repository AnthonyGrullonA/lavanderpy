import logging
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)

User = get_user_model()


class CashRegister(models.Model):
    """
    Caja (de día o turno). Solo debe existir UNA abierta a la vez.
    """
    name = models.CharField(max_length=50, unique=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)

    opened_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="cash_opened"
    )
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="cash_closed",
        null=True, blank=True
    )

    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-opened_at"]
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"

    def __str__(self) -> str:
        return f"Caja {self.name} ({'Abierta' if self.is_open else 'Cerrada'})"

    # --- Helpers de negocio ---
    @property
    def ingresos(self) -> Decimal:
        return self.movements.filter(movement_type="ingreso").aggregate(
            s=models.Sum("amount")
        )["s"] or Decimal("0.00")

    @property
    def egresos(self) -> Decimal:
        return self.movements.filter(movement_type="egreso").aggregate(
            s=models.Sum("amount")
        )["s"] or Decimal("0.00")

    @property
    def balance_actual(self) -> Decimal:
        return self.opening_balance + self.ingresos - self.egresos

    def close(self, user: AbstractBaseUser) -> None:
        """
        Cierra la caja calculando el balance final.
        """
        if not self.is_open:
            logger.warning(f"[CASH] Intento de cerrar caja ya cerrada: {self}")
            return

        self.closing_balance = self.balance_actual
        self.closed_at = timezone.now()
        self.closed_by = user
        self.is_open = False
        self.save(update_fields=["closing_balance", "closed_at", "closed_by", "is_open"])
        logger.info(f"[CASH] Caja '{self.name}' cerrada con balance RD$ {self.closing_balance:.2f}")


class CashMovement(models.Model):
    """
    Movimiento de caja: ingreso (pago de orden, otros), egreso (gasto).
    """
    MOVEMENT_TYPES = [
        ("ingreso", "Ingreso"),
        ("egreso", "Egreso"),
    ]

    register = models.ForeignKey(
        CashRegister, on_delete=models.CASCADE, related_name="movements"
    )
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    # Opcional: vínculo con orden
    related_order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Movimiento de caja"
        verbose_name_plural = "Movimientos de caja"

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} - RD${self.amount} ({self.description})"

    def save(self, *args, **kwargs) -> None:
        if self.amount <= 0:
            raise ValueError("El monto del movimiento debe ser mayor que cero.")
        super().save(*args, **kwargs)
        logger.info(
            f"[CASH] Movimiento '{self.movement_type}' RD${self.amount:.2f} "
            f"en '{self.register.name}' por {self.created_by} "
            f"{'(orden ' + self.related_order.code + ')' if self.related_order_id else ''}"
        )
