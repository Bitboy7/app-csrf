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
from .forms import *
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404

@login_required
def index(request):
    consultas = Consulta.objects.all()
    doctores = Doctor.objects.all()
    pacientes = Paciente.objects.all()
    form = ConsultaForm()  # Crear una instancia del formulario
    return render(request, 'index.html', {'consultas': consultas, 'form': form, 'doctores': doctores, 'pacientes': pacientes})  # Pasar el formulario al contexto

# Login, registro, logout
def user_login(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirigir al ínicio si ya ha iniciado sesión

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
    if request.user.is_authenticated:
        return redirect('index')  # Redirect to index if already logged in

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
    request.session.flush()  # Destroy all session data
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

# Consultas
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
def consulta_edit(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta actualizada correctamente.')
            return redirect('index')
    else:
        form = ConsultaForm(instance=consulta)
    return render(request, 'consulta_form.html', {'form': form})

@login_required
def consulta_delete(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    consulta.delete()
    messages.success(request, 'Consulta eliminada correctamente.')
    return redirect('index')

# Doctores
@login_required
def doctor_create(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor creado correctamente.')
            return redirect('index')
    else:
        form = DoctorForm()
    return render(request, 'doctor_form.html', {'form': form})

@login_required
def doctor_edit(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor actualizado correctamente.')
            return redirect('index')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'doctor_form.html', {'form': form})

@login_required
def doctor_delete(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.delete()
    messages.success(request, 'Doctor eliminado correctamente.')
    return redirect('index')

# Pacientes
@login_required
def paciente_create(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente creado correctamente.')
            return redirect('index')
    else:
        form = PacienteForm()
    return render(request, 'paciente_form.html', {'form': form})

@login_required
def paciente_edit(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente actualizado correctamente.')
            return redirect('index')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'paciente_form.html', {'form': form})

@login_required
def paciente_delete(request, paciente_id):
    if request.method == 'POST':
        paciente = get_object_or_404(Paciente, id=paciente_id)
        paciente.delete()
        messages.success(request, 'Paciente eliminado correctamente.')
    return redirect('index')