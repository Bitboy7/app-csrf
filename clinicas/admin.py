from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Doctor, Paciente, Consulta, Usuario

admin.site.register(Doctor)
admin.site.register(Paciente)
admin.site.register(Consulta)
admin.site.register(Usuario, UserAdmin)
