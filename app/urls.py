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
]

# Servir archivos media durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)