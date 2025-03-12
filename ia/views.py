# Core Django imports
import logging
logger = logging.getLogger(__name__)
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from .forms import MedicamentoForm, MovimientoStockForm
from .models import Medicamento
from django.core.mail import send_mail
from django.conf import settings
# AI
from .assist_agent import get_medical_response, reset_assistant, change_provider
from .models import ChatbotLog
from .data_analysis_agent import analyze_patient_data, analyze_general_medical_data
# PDF
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from django.utils import timezone
#Agente 
from .stock_agent import analyze_medication_stock

# Chatbot
@login_required
def chatbot_view(request):
    """Vista para renderizar la página del chatbot"""
    return render(request, 'ia/chatbot.html')

@csrf_protect
def chatbot_api(request):
    """API para procesar mensajes del chatbot"""
    if request.method == 'POST':
        message = request.POST.get('message', '')
        provider = request.POST.get('provider', None)
        change_provider_flag = request.POST.get('change_provider', False)
        
        # Obtener el nombre del usuario
        user_name = None
        if request.user.is_authenticated:
            user_name = request.user.first_name or request.user.username
        
        if change_provider_flag and provider:
            # Cambiar el proveedor y reiniciar
            response = change_provider(provider)
            reset_assistant(provider)
            return JsonResponse({'response': response})
        elif message.lower() == 'reset':
            response = reset_assistant(provider)
        else:
            response = get_medical_response(message, provider, user_name)
        
        # Guardar la llamada en la base de datos solo si la respuesta es válida
        if response and response != "Lo siento, tuve un problema para procesar tu pregunta.":
            ChatbotLog.objects.create(
                user=request.user,
                provider=provider or "default",
                message=message,
                response=response
            )
        
        return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def chat_history(request):
    """Vista para mostrar el historial de chats del usuario"""
    chats = ChatbotLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'ia/history.html', {'chats': chats})

@login_required
def delete_chat(request, chat_id):
    """Eliminar un chat específico"""
    chat = get_object_or_404(ChatbotLog, id=chat_id, user=request.user)
    chat.delete()
    messages.success(request, "Chat eliminado correctamente.")
    return redirect('chat_history')

@login_required
def delete_all_chats(request):
    """Eliminar todo el historial de chats del usuario"""
    if request.method == 'POST':
        ChatbotLog.objects.filter(user=request.user).delete()
        messages.success(request, "Todo el historial de chats ha sido eliminado.")
    return redirect('chat_history')

# Analysis
@login_required
def data_analysis_view(request):
    """Vista para la página de análisis de datos"""
    return render(request, 'ia/dashboard.html')

@login_required
def patient_analysis_view(request, patient_id):
    """Vista para el análisis individual de un paciente"""
    from clinicas.models import Paciente
    
    try:
        patient = Paciente.objects.get(id=patient_id)
        analysis = None
        
        if request.method == 'POST':
            # Realizar análisis
            analysis = analyze_patient_data(patient_id)
        
        return render(request, 'ia/patient_analysis.html', {
            'patient': patient,
            'analysis': analysis
        })
    except Paciente.DoesNotExist:
        messages.error(request, "Paciente no encontrado.")
        return redirect('data_analysis_view')
    
@login_required
@csrf_protect
def general_analysis_api(request):
    """API para el análisis general de datos médicos"""
    if request.method == 'POST':
        query_type = request.POST.get('query_type')
        
        if query_type:
            analysis = analyze_general_medical_data(query_type)
            return JsonResponse({'analysis': analysis})
        
    return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

# Añadir estas nuevas vistas para generar PDFs
@login_required
def print_patient_analysis(request, patient_id):
    """Genera un PDF del análisis de paciente"""
    from clinicas.models import Paciente
    
    try:
        patient = Paciente.objects.get(id=patient_id)
        analysis = analyze_patient_data(patient_id)
        
        # Preparar el contexto para la plantilla
        context = {
            'patient': patient,
            'analysis': analysis,
            'fecha_impresion': timezone.now(),
            'usuario': request.user,
            'tipo_analisis': 'paciente'
        }
        
        # Renderizar la plantilla HTML
        html_string = render_to_string('pdf/analysis_pdf.html', context)
        
        # Configurar fuentes
        font_config = FontConfiguration()
        
        # Crear PDF con WeasyPrint
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf_file = BytesIO()
        html.write_pdf(pdf_file, font_config=font_config)
        
        # Preparar y devolver la respuesta HTTP con el PDF
        pdf_file.seek(0)
        filename = f"analisis_paciente_{patient.nombre}_{patient.id}.pdf"
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Paciente.DoesNotExist:
        messages.error(request, "Paciente no encontrado.")
        return redirect('data_analysis_view')

@login_required
def print_general_analysis(request):
    """Genera un PDF del análisis general seleccionado"""
    query_type = request.GET.get('type')
    
    if not query_type:
        messages.error(request, "Tipo de análisis no especificado.")
        return redirect('data_analysis_view')
    
    # Realizar análisis
    analysis = analyze_general_medical_data(query_type)
    
    # Título del análisis según el tipo
    titles = {
        'tendencias_sintomas': 'Tendencias en Síntomas Reportados',
        'eficacia_tratamientos': 'Eficacia de Tratamientos',
        'distribucion_genero_edad': 'Distribución Demográfica de Pacientes'
    }
    
    # Preparar el contexto para la plantilla
    context = {
        'analysis_title': titles.get(query_type, 'Análisis General'),
        'analysis': analysis,
        'fecha_impresion': timezone.now(),
        'usuario': request.user,
        'tipo_analisis': 'general'
    }
    
    # Renderizar la plantilla HTML
    html_string = render_to_string('pdf/analysis_pdf.html', context)
    
    # Configurar fuentes
    font_config = FontConfiguration()
    
    # Crear PDF con WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = BytesIO()
    html.write_pdf(pdf_file, font_config=font_config)
    
    # Preparar y devolver la respuesta HTTP con el PDF
    pdf_file.seek(0)
    filename = f"analisis_general_{query_type}.pdf"
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# stock management
@login_required
def medicamento_list(request):
    """Lista de medicamentos con filtro de estado"""
    estado_filtro = request.GET.get('estado', '')
    
    medicamentos = Medicamento.objects.all()
    if estado_filtro:
        if estado_filtro == 'bajo':
            medicamentos = medicamentos.filter(cantidad_actual__lte=models.F('cantidad_minima'), cantidad_actual__gt=0)
        elif estado_filtro == 'agotado':
            medicamentos = medicamentos.filter(cantidad_actual__lte=0)
    
    return render(request, 'stock/medicamento_list.html', {
        'medicamentos': medicamentos,
        'estado_filtro': estado_filtro
    })

@login_required
def medicamento_create(request):
    """Crear nuevo medicamento"""
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            medicamento = form.save(commit=False)
            medicamento.created_by = request.user
            medicamento.save()
            messages.success(request, 'Medicamento creado correctamente.')
            return redirect('medicamento_list')
    else:
        form = MedicamentoForm()
    
    return render(request, 'forms/medicamento_form.html', {'form': form})

@login_required
def medicamento_edit(request, medicamento_id):
    """Editar medicamento existente"""
    medicamento = get_object_or_404(Medicamento, id=medicamento_id)
    
    if request.method == 'POST':
        form = MedicamentoForm(request.POST, instance=medicamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicamento actualizado correctamente.')
            return redirect('medicamento_list')
    else:
        form = MedicamentoForm(instance=medicamento)
    
    return render(request, 'forms/medicamento_form.html', {'form': form, 'medicamento': medicamento})

@login_required
def movimiento_create(request):
    """Registrar un nuevo movimiento de stock"""
    if request.method == 'POST':
        form = MovimientoStockForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.created_by = request.user
            movimiento.save()  # El método save() del modelo actualizará el stock del medicamento
            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('medicamento_list')
    else:
        form = MovimientoStockForm()
    
    return render(request, 'forms/movimiento_form.html', {'form': form})

@login_required
def medicamento_historial(request, medicamento_id):
    """Ver historial de movimientos de un medicamento"""
    medicamento = get_object_or_404(Medicamento, id=medicamento_id)
    movimientos = medicamento.movimientos.all().order_by('-fecha')
    
    # Pre-calculate counts
    entradas_count = movimientos.filter(tipo='entrada').count()
    salidas_count = movimientos.filter(tipo='salida').count()
    
    return render(request, 'stock/medicamento_historial.html', {
        'medicamento': medicamento,
        'movimientos': movimientos,
        'entradas_count': entradas_count,
        'salidas_count': salidas_count
    })
    
@login_required
def medication_stock_analysis(request):
    """Vista para el análisis de stock de medicamentos"""
    return render(request, 'ia/medication_stock.html')

@login_required
@require_POST
def medication_stock_api(request):
    """API endpoint for medication stock analysis"""
    query_type = request.POST.get('query_type')
    
    if not query_type:
        return JsonResponse({'error': 'Tipo de análisis no especificado'}, status=400)
    
    try:
        # Use our fixed analysis function from stock_agent.py
        from .stock_agent import analyze_medication_stock
        analysis = analyze_medication_stock(query_type)
        
        return JsonResponse({
            'success': True,
            'analysis': analysis,
            'query_type': query_type
        })
    except Exception as e:
        logger.error(f"Error in medication_stock_api: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def print_medication_analysis(request):
    """Genera un PDF del análisis de medicamentos seleccionado"""
    query_type = request.GET.get('type')
    
    if not query_type:
        messages.error(request, "Tipo de análisis no especificado.")
        return redirect('medication_stock_analysis')
    
    # Realizar análisis
    analysis = analyze_medication_stock(query_type)
    
    # Título del análisis según el tipo
    titles = {
        'alertas_stock': 'Alertas de Stock Bajo',
        'patrones_consumo': 'Análisis de Patrones de Consumo',
        'estacionalidad': 'Análisis de Estacionalidad'
    }
    
    # Preparar el contexto para la plantilla
    context = {
        'analysis_title': titles.get(query_type, 'Análisis de Medicamentos'),
        'analysis': analysis,
        'fecha_impresion': timezone.now(),
        'usuario': request.user,
        'tipo_analisis': 'medicamentos'
    }
    
    # Renderizar la plantilla HTML
    html_string = render_to_string('pdf/analysis_pdf.html', context)
    
    # Configurar fuentes
    font_config = FontConfiguration()
    
    # Crear PDF usando WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = BytesIO()
    html.write_pdf(pdf_file, font_config=font_config)
    
    # Preparar y devolver la respuesta HTTP con PDF
    pdf_file.seek(0)
    filename = f"analisis_medicamentos_{query_type}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def stock_alert_config(request):
    """Configuración de alertas de stock"""
    # Obtener la configuración actual del usuario o valores predeterminados
    try:
        config = AlertConfiguration.objects.filter(user=request.user).first()
    except:
        config = None
    
    if request.method == 'POST':
        # Si es una solicitud POST, procesar el formulario
        notify_low_stock = request.POST.get('notify_low_stock') == 'on'
        threshold_percentage = int(request.POST.get('threshold_percentage', 100))
        email_notifications = request.POST.get('email_notifications') == 'on'
        
        if config:
            # Actualizar configuración existente
            config.notify_low_stock = notify_low_stock
            config.threshold_percentage = threshold_percentage
            config.email_notifications = email_notifications
            config.save()
        else:
            # Crear nueva configuración
            from .models import AlertConfiguration
            AlertConfiguration.objects.create(
                user=request.user,
                notify_low_stock=notify_low_stock,
                threshold_percentage=threshold_percentage,
                email_notifications=email_notifications
            )
        
        messages.success(request, 'Configuración de alertas actualizada correctamente.')
        return redirect('stock_alert_config')
    
    return render(request, 'stock/alert_config.html', {'config': config})

def send_stock_alert_email(user, medicamentos_bajos):
    """Envía alertas de stock bajo por correo electrónico"""
    if not user.email:
        return False
    
    subject = "Alerta de Stock Bajo - Sistema de Gestión de Clínica"
    message = f"Hola {user.get_full_name() or user.username},\n\n"
    message += "Los siguientes medicamentos están por debajo del nivel mínimo de stock:\n\n"
    
    for med in medicamentos_bajos:
        message += f"• {med.nombre} ({med.presentacion})\n"
        message += f"  Stock actual: {med.cantidad_actual} | Stock mínimo: {med.cantidad_minima}\n\n"
    
    message += "\nPor favor, considere reabastecer estos productos pronto.\n\n"
    message += "Saludos,\nSistema de Gestión de Clínica"
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando alerta por email: {str(e)}")
        return False