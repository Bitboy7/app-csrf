from django.contrib import admin

# Register your models here.
from .models import Laboratorio, Medicamento, MovimientoStock

admin.site.register(Laboratorio)    
admin.site.register(Medicamento)
admin.site.register(MovimientoStock)