from django.db import models
from clinicas.models import Usuario, Consulta
from django.utils import timezone
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

# Create your models here.
class ChatbotLog(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    provider = models.CharField(max_length=50)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Log {self.id} - {self.user} - {self.timestamp}'

class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='laboratorios_creados')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre   
    
class Medicamento(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    presentacion = models.CharField(max_length=50)
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE, related_name='medicamentos')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_actual = models.IntegerField(default=0)
    cantidad_minima = models.IntegerField(default=10)
    fecha_ultima_reposicion = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='medicamentos_creados')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.presentacion})"
    
    @property
    def estado_stock(self):
        if self.cantidad_actual <= 0:
            return "agotado"
        elif self.cantidad_actual <= self.cantidad_minima:
            return "bajo"
        else:
            return "normal"
    
class MovimientoStock(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    )
    
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name='movimientos')
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    motivo = models.CharField(max_length=100, blank=True, null=True)
    consulta = models.ForeignKey(Consulta, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    
    def save(self, *args, **kwargs):
        # Actualizar el stock del medicamento
        if self.tipo == 'entrada':
            self.medicamento.cantidad_actual += self.cantidad
            if not self.motivo:
                self.motivo = "Reposición de stock"
            self.medicamento.fecha_ultima_reposicion = timezone.now().date()
        else:
            self.medicamento.cantidad_actual -= self.cantidad
            if not self.motivo:
                self.motivo = "Consumo"
        
        self.medicamento.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicamento.nombre}: {self.tipo} de {self.cantidad} ({self.fecha.strftime('%d/%m/%Y')})"
    
    
class AlertConfiguration(models.Model):
    """Configuración de alertas de stock para usuarios"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notify_low_stock = models.BooleanField(default=True)
    threshold_percentage = models.IntegerField(default=100)  # 100% significa alertar cuando alcanza stock_minimo
    email_notifications = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Configuración de alertas"
        verbose_name_plural = "Configuraciones de alertas"