from django.db import models
from clinicas.models import Usuario

# Create your models here.
class ChatbotLog(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    provider = models.CharField(max_length=50)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Log {self.id} - {self.user} - {self.timestamp}'