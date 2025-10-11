from django import forms
from .models import InventoryItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "unit",
            "description",
            "current_stock",
            "min_stock",
            "cost_per_unit",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Detergente líquido"
            }),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2
            }),
            "current_stock": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "min_stock": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "cost_per_unit": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
        }

    def clean_current_stock(self):
        stock = self.cleaned_data.get("current_stock", 0)
        if stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # is_active = True por defecto al crear un insumo
        if not self.instance.pk:
            self.instance.is_active = True
