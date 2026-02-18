from .models import DepartmentSettings

def department_settings(request):
    """
    Adds DepartmentSettings (singleton) to all templates.
    """
    settings = DepartmentSettings.objects.first()
    return {"department_settings": settings}
