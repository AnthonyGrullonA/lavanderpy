from django import forms
from .models import Order, OrderLine
from customers.models import Customer
from catalog.models import Service


class OrderForm(forms.ModelForm):
    """Formulario principal de la orden (sin líneas)."""
    class Meta:
        model = Order
        fields = [
            "customer",
            "delivery_type",
            "status",
            "notes",
        ]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "delivery_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opciones ordenadas para facilidad de selección
        self.fields["customer"].queryset = Customer.objects.filter(is_active=True).order_by("name")
        self.fields["status"].label = "Estado de la orden"
        self.fields["delivery_type"].label = "Tipo de entrega"
        self.fields["notes"].label = "Notas adicionales"


class OrderLineForm(forms.ModelForm):
    """Formulario individual de línea de pedido."""
    class Meta:
        model = OrderLine
        fields = [
            "service",
            "quantity",
            "price",
        ]
        widgets = {
            "service": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1", "step": "1"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True).order_by("name")

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity", 0)
        if qty <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return qty
