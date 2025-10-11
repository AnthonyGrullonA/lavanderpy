from .models import Theme

def active_theme(request):
    """Provee el tema activo a todas las plantillas."""
    return {"active_theme": Theme.objects.filter(is_active=True).first()}
