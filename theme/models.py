import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image


def upload_logo_path(instance, filename):
    return os.path.join("theme", "logos", filename)


def upload_favicon_path(instance, filename):
    return os.path.join("theme", "favicons", filename)


def upload_preloader_path(instance, filename):
    return os.path.join("theme", "preloaders", filename)


class Theme(models.Model):
    name = models.CharField(max_length=100, default="Trezo", verbose_name="Nombre del sistema")
    tagline = models.CharField(max_length=150, blank=True, null=True)
    logo = models.ImageField(upload_to=upload_logo_path, blank=True, null=True)
    favicon = models.ImageField(upload_to=upload_favicon_path, blank=True, null=True)
    preloader_text = models.CharField(max_length=50, default="TREZO")
    footer_text = models.CharField(max_length=200, default="© Trezo - 2025")
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.is_active and Theme.objects.exclude(pk=self.pk).filter(is_active=True).exists():
            raise ValidationError("Ya existe un tema activo. Solo uno puede estarlo.")

    def save(self, *args, **kwargs):
        """Guarda el tema y convierte/redimensiona imágenes."""
        if self.is_active:
            Theme.objects.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

        # Procesar logo
        if self.logo:
            self._resize_image(self.logo, max_size=(300, 300))  # tamaño visible sin deformar

        # Procesar favicon
        if self.favicon:
            self._resize_image(self.favicon, max_size=(64, 64), convert_to="PNG")  # favicon pequeño y cuadrado

    def _resize_image(self, field, max_size=(300, 300), convert_to=None):
        """Redimensiona y opcionalmente convierte la imagen a PNG."""
        try:
            img = Image.open(field.path)
        except Exception:
            return  # si no es imagen válida, lo deja

        # Convertir a modo RGB (evita errores con transparencia)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if convert_to == "PNG" else "RGB")

        # Redimensionar
