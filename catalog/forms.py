from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "name",
            "category",
            "description",
            "unit_type",
            "base_price",
            "estimated_time_minutes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Descripción breve del servicio"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personaliza los labels y estilos
        self.fields["name"].label = "Nombre del servicio"
        self.fields["category"].label = "Categoría"
        self.fields["unit_type"].label = "Tipo de unidad"
        self.fields["base_price"].label = "Precio base (RD$)"
        self.fields["estimated_time_minutes"].label = "Duración estimada (minutos)"

        # Aplica clases CSS uniformes
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-control"})
            else:
                field.widget.attrs.update({"class": "form-select"})

        # Valor inicial si el servicio es nuevo
        if not self.instance.pk:
            self.instance.is_active = True
