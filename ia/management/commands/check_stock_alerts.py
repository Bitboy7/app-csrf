from django.core.management.base import BaseCommand
from django.db.models import F
from django.conf import settings
from ia.models import AlertConfiguration, Medicamento
from ia.views import send_stock_alert_email

class Command(BaseCommand):
    help = 'Verifica stock bajo y envía alertas por email'

    def handle(self, *args, **options):
        self.stdout.write('Verificando stock bajo y enviando alertas...')
        
        # Obtener configuraciones de usuarios que quieren alertas por email
        configs = AlertConfiguration.objects.filter(
            notify_low_stock=True,
            email_notifications=True
        ).select_related('user')
        
        if not configs.exists():
            self.stdout.write(self.style.WARNING('No hay usuarios con alertas configuradas'))
            return
            
        self.stdout.write(f'Encontrados {configs.count()} usuarios con alertas configuradas')
        
        for config in configs:
            user = config.user
            if not user.email:
                self.stdout.write(self.style.WARNING(
                    f'El usuario {user.username} no tiene email configurado'
                ))
                continue
                
            threshold = config.threshold_percentage / 100
            
            # Obtener medicamentos con stock bajo según el umbral personalizado
            medicamentos_bajos = Medicamento.objects.filter(
                cantidad_actual__lte=F('cantidad_minima') * threshold
            ).order_by('cantidad_actual')
            
            if medicamentos_bajos.exists():
                self.stdout.write(f'Encontrados {medicamentos_bajos.count()} medicamentos con stock bajo para {user.username}')
                
                # Enviar email
                sent = send_stock_alert_email(user, medicamentos_bajos)
                if sent:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Alerta enviada a {user.email}'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'❌ No se pudo enviar alerta a {user.email}'
                    ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'No hay medicamentos con stock bajo para el usuario {user.username}'
                ))
        
        self.stdout.write(self.style.SUCCESS('Proceso de verificación completado'))