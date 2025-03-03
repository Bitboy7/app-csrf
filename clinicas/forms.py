from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import Paciente, Usuario, Consulta

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ['doctor', 'paciente', 'fecha', 'motivo', 'diagnostico']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'motivo': forms.Textarea(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
            'diagnostico': forms.Textarea(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Nombre de usuario'}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Contraseña'}),
    )

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Correo electrónico'})
    )
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Nombre de usuario'})
    )
    password1 = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Contraseña'})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Confirmar contraseña'})
    )
    telefono = forms.CharField(
        max_length=15, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Teléfono'})
    )
    fecha_nacimiento = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'type': 'date'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2', 'telefono', 'fecha_nacimiento']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2
        
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo debe contener números.")
        return telefono
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.telefono = self.cleaned_data.get('telefono', '')
        user.fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if commit:
            user.save()
        return user

# Añade esta nueva clase de formulario
class CambioPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Contraseña actual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Nueva contraseña'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Confirmar nueva contraseña'
        })
        
class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Apellidos'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Correo electrónico'})
    )
    telefono = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Teléfono'})
    )
    direccion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'placeholder': 'Dirección'})
    )
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline', 'type': 'date'})
    )
    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'})
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'fecha_nacimiento', 'foto_perfil']