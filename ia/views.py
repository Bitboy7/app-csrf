from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# AI
from .ia_agent import get_medical_response, reset_assistant, change_provider
from .models import ChatbotLog

# Chatbot
@login_required
def chatbot_view(request):
    """Vista para renderizar la página del chatbot"""
    return render(request, 'chat/chatbot.html')

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
    return render(request, 'chat/history.html', {'chats': chats})

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