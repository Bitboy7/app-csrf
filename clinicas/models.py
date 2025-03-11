from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)

    # Define custom related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='grupos',
        blank=True,
        help_text='Los grupos a los que pertenece este usuario. Un usuario obtendrá todos los permisos otorgados a cada uno de sus grupos.',
        related_name='usuario_set',  # Nombre relacionado personalizado
        related_query_name='usuario'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='permisos de usuario',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        related_name='usuario_set',  # Nombre relacionado personalizado
        related_query_name='usuario'
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios' 
        
class Doctor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, default='', blank=True)
    especialidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    nacimiento = models.DateField(default='2000-01-01', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.nombre} - {self.especialidad}'

class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    paterno = models.CharField(max_length=100, blank=True)
    materno = models.CharField(max_length=100, blank=True, null=True)  
    fecha_nacimiento = models.DateField(default='2000-01-01')
    telefono = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genero = models.CharField(max_length=1, choices=(('M', 'Masculino'), ('F', 'Femenino')), default='M')

    def __str__(self):
         return f'{self.nombre} - {self.fecha_nacimiento}'

class Consulta(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    motivo = models.TextField(default='')
    diagnostico = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.fecha} - {self.doctor} - {self.paciente}'
    
class HistorialMedico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historiales')
    consulta = models.ForeignKey(Consulta, on_delete=models.SET_NULL, null=True, blank=True, related_name='historiales')
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    tratamiento = models.TextField(blank=True)
    notas = models.TextField(blank=True, null=True)
    archivos = models.FileField(upload_to='historiales/', null=True, blank=True)
    created_by = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='historiales_creados')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Historial de {self.paciente} - {self.fecha}'
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Historial Médico'
        verbose_name_plural = 'Historiales Médicos'