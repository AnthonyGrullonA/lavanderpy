from django import forms
from .models import Customer  # asumiendo que tu modelo se llama así

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "customer_type",
            "email",
            "phone",
            "address",
            "contact_person",
            "credit_limit",
        ]  # Omitimos is_active

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valor por defecto para nuevos registros
        if not self.instance.pk:
            self.instance.is_active = True
