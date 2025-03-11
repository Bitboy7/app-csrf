# App-CSRF - Sistema de Gestión para Clínicas

Este proyecto es un sistema web para la gestión de clínicas médicas que permite administrar doctores, pacientes y consultas. Desarrollado con Django 5.1.6 y MySQL.

## Características

- Gestión de usuarios con diferentes permisos
- Registro y autenticación de usuarios
- Perfiles de usuario personalizables
- Administración de doctores y pacientes
- Programación y seguimiento de consultas médicas
- Generación de historiales médicos en PDF
- Interfaz responsiva con Tailwind CSS

## Requisitos previos

- Python 3.11 o superior
- MySQL 8.0 o superior
- Poetry (gestor de dependencias para Python)
- Navegador web moderno
- GTK+ para WeasyPrint (ver instrucciones específicas abajo)

## Instalación

1. Clonar el repositorio
   ```bash
   git clone https://github.com/tu-usuario/app-csrf.git
   cd app-csrf
   ```
2. Configurar entorno virtual con Poetry
   ```bash
   poetry install
   ```
3. Configurar archivo `.env`

   Crea un archivo `.env` en la raíz del proyecto con la siguiente información:

   ```env
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   DB_NAME=nombre_base_datos
   DB_USER=usuario_base_datos
   DB_PASSWORD=contraseña_base_datos
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. Configurar la base de datos
   ```bash
   poetry run python manage.py migrate
   ```
5. Crear usuario administrador
   ```bash
   poetry run python manage.py createsuperuser
   ```
6. Recopilar archivos estáticos
   ```bash
   poetry run python manage.py collectstatic
   ```
7. Ejecutar el servidor de desarrollo
   ```bash
   poetry run python manage.py runserver
   ```

## Instalación de WeasyPrint

WeasyPrint requiere bibliotecas del sistema adicionales para funcionar correctamente:

### Instalar GTK+ para Windows

Descarga e instala el paquete GTK para Windows desde aquí: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

Después de instalar, asegúrate de agregar la carpeta bin de GTK a tu variable de entorno PATH

## Uso

1. Accede a `http://127.0.0.1:8000/` en tu navegador
2. Inicia sesión con el usuario administrador o regístrate como nuevo usuario
3. Navega por las diferentes secciones:
   - **Panel principal**: Vista general de doctores, pacientes y consultas
   - **Doctores**: Gestión de información médica
   - **Pacientes**: Registro y seguimiento
   - **Consultas**: Programación e historial

## Configuración de Seguridad

Para entornos de producción, asegúrate de:

- Cambiar `DEBUG = False` en `settings.py`
- Generar una nueva `SECRET_KEY` segura
- Configurar correctamente `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`
- Usar HTTPS para todas las conexiones

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
