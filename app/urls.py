"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from clinicas import views
from ia import views as ia_views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # Ruta principal
    path('login/', views.user_login, name='login'),  # Ruta para el login
    path('register/', views.user_register, name='register'),  # Ruta para el registro
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # Ruta para el logout
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),  # Nueva ruta para cambiar contraseña
    path('perfil/', views.perfil_usuario, name='perfil'),  # Nueva ruta para el perfil
    path('consulta/create/', views.consulta_create, name='consulta_create'),  # Nueva ruta para crear consulta
    path('doctor/create/', views.doctor_create, name='doctor_create'),  # Nueva ruta para crear Doctores
    path('paciente/create/', views.paciente_create, name='paciente_create'), 
    path('consulta/nueva/', views.consulta_create, name='consulta_create'),
    path('consulta/editar/<int:consulta_id>/', views.consulta_edit, name='consulta_edit'),
    path('consulta/borrar/<int:consulta_id>/', views.consulta_delete, name='consulta_delete'), 
    path('doctor/editar/<int:doctor_id>/', views.doctor_edit, name='doctor_edit'),
    path('doctor/borrar/<int:doctor_id>/', views.doctor_delete, name='doctor_delete'),
    path('paciente/editar/<int:paciente_id>/', views.paciente_edit, name='paciente_edit'),
    path('paciente/borrar/<int:paciente_id>/', views.paciente_delete, name='paciente_delete'),
    path('paciente/<int:paciente_id>/', views.paciente_detalle, name='paciente_detalle'),
    path('paciente/<int:paciente_id>/historial/add/', views.historial_create, name='historial_create'),
    path('paciente/<int:paciente_id>/historial/pdf/', views.imprimir_historial, name='imprimir_historial'),
    path('paciente/editar/<int:historialmedico_id>/historial/', views.historial_edit, name='historial_edit'),
    # chatbot
    path('chatbot/', ia_views.chatbot_view, name='chatbot'),
    path('chatbot/history/', ia_views.chat_history, name='chat_history'),
    path('chatbot/delete/<int:chat_id>/', ia_views.delete_chat, name='delete_chat'),
    path('chatbot/delete-all/', ia_views.delete_all_chats, name='delete_all_chats'),
    path('api/chatbot/', ia_views.chatbot_api, name='chatbot_api'),

]

# Servir archivos media durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)