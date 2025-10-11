from django import forms
from .models import CashMovement


class CashMovementForm(forms.ModelForm):
    """Formulario para registrar movimientos manuales (ingresos/egresos)."""
    class Meta:
        model = CashMovement
        fields = ["movement_type", "amount", "description", "related_order"]
        widgets = {
            "movement_type": forms.Select(attrs={"class": "form-select h-55"}),
            "amount": forms.NumberInput(attrs={"class": "form-control h-55", "step": "0.01", "min": "0"}),
            "description": forms.TextInput(attrs={"class": "form-control h-55", "placeholder": "Descripción del movimiento"}),
            "related_order": forms.Select(attrs={"class": "form-select h-55"}),
        }
        labels = {
            "movement_type": "Tipo de movimiento",
            "amount": "Monto (RD$)",
            "description": "Descripción",
            "related_order": "Orden relacionada (opcional)",
        }
