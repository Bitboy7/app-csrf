# Core Django imports
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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

