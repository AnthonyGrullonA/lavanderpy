# customers/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    class CustomerType(models.TextChoices):
        PERSONAL = "personal", _("Personal")
        BUSINESS = "business", _("Empresarial")
        DELIVERY = "delivery", _("Delivery")

    name = models.CharField(_("Nombre completo / Empresa"), max_length=150)
    customer_type = models.CharField(
        _("Tipo de cliente"),
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.PERSONAL
    )
    email = models.EmailField(_("Correo electrónico"), blank=True, null=True)
    phone = models.CharField(_("Teléfono"), max_length=20, blank=True, null=True)
    address = models.TextField(_("Dirección"), blank=True, null=True)
    contact_person = models.CharField(
        _("Persona de contacto (si aplica)"),
        max_length=100,
        blank=True,
        null=True
    )
    credit_limit = models.DecimalField(_("Límite de crédito"), max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(_("Balance actual"), max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Fecha de registro"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última actualización"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")

    def __str__(self):
        return self.name

    def deactivate(self):
        """Desactiva el cliente en lugar de eliminarlo."""
        self.is_active = False
        self.save()
