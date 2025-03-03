#Django packages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt, csrf_protect
# clinicas/models.py
from .models import Consulta, Paciente, Doctor
#clinicas/forms.py
from .forms import LoginForm, RegistroForm, CambioPasswordForm, PerfilForm, ConsultaForm
from django.contrib.auth import logout

@login_required(login_url='/login')
def index(request):
    consultas = Consulta.objects.all()
    doctores = Doctor.objects.all()
    pacientes = Paciente.objects.all()
    form = ConsultaForm()  # Crear una instancia del formulario
    return render(request, 'index.html', {'consultas': consultas, 'form': form, 'doctores': doctores, 'pacientes': pacientes})  # Pasar el formulario al contexto

# Login, registro
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('/admin')
                else:
                    return redirect('index')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            telefono = form.cleaned_data.get('telefono')
            direccion = form.cleaned_data.get('direccion')
            fecha_nacimiento = form.cleaned_data.get('fecha_nacimiento')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Cuenta creada para {username}. ¡Bienvenido!')
                return redirect('index')
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

# Cambiar contraseña, perfil
@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = CambioPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            messages.success(request, 'Tu contraseña fue actualizada correctamente!')
            return redirect('index')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = CambioPasswordForm(request.user)
    return render(request, 'cambiar_pass.html', {'form': form})

@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'perfil.html', {'form': form})

# Consultas y pacientes
@login_required
def consulta_create(request):
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta creada correctamente.')
            return redirect('index')
    else:
        form = ConsultaForm()
    return render(request, 'consulta_form.html', {'form': form})

@login_required
def consulta_update(request, id):
    consulta = Consulta.objects.get(id=id)
    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta actualizada correctamente.')
            return redirect('index')
    else:
        form = ConsultaForm(instance=consulta)
    return render(request, 'consulta_form.html', {'form': form})
