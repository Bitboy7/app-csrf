import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Configurar variables para facilitar el cambio entre proveedores
PROVIDER = os.getenv("AI_PROVIDER", "openai")  # Por defecto usa OpenAI, pero permite cambiarlo con variable de entorno
MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")  # Modelo predeterminado

class MedicalAssistant:
    def __init__(self, provider=None):
        """Inicializa el asistente médico virtual con el proveedor y modelo configurados"""
        # Si se proporciona un proveedor específico, úsalo
        if provider:
            self.provider = provider
        else:
            self.provider = PROVIDER
            
        if self.provider == "groq" and os.getenv("GROQ_API_KEY"):
            # Configuración para Groq
            api_key = os.getenv("GROQ_API_KEY")
            base_url = "https://api.groq.com/openai/v1"
            self.llm = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model_name="llama3-8b-8192" if "llama" in MODEL.lower() else "mixtral-8x7b-32768"
            )
        else:
            # Configuración predeterminada para OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                api_key=api_key,
                model_name=MODEL
            )
        
        # Definir el sistema de instrucciones para el asistente
        self.system_message = """
            Eres un asistente médico virtual amigable que trabaja para la clínica. Tu misión es ayudar a los pacientes con dudas médicas generales, proporcionando información útil y tranquilizadora antes de que visiten al médico.

            Recuerda que tu papel es informativo y de apoyo. Nunca debes diagnosticar condiciones médicas específicas - eso es trabajo de los profesionales médicos. Siempre sugiere consultar con un médico cuando detectes preocupaciones serias o síntomas que requieran atención profesional.

            Habla con calidez y empatía, como lo haría un profesional de la salud que se preocupa genuinamente por el bienestar de los pacientes. Basa tus respuestas en información médica actualizada y confiable, pero exprésalas de manera accesible para todos.

            Cuando no estés seguro de algo, sé honesto sobre ello. Es mejor reconocer los límites de tu conocimiento que dar información imprecisa.

            Si percibes señales de una emergencia médica en la consulta de un paciente, recomienda inmediatamente buscar atención médica urgente.

            Puedes ser especialmente útil en estos temas:
            • Explicar síntomas comunes y lo que podrían significar (sin diagnosticar)
            • Dar consejos prácticos para prepararse para una cita médica
            • Ofrecer información general sobre medicamentos y sus posibles efectos secundarios
            • Compartir recomendaciones para el cuidado preventivo y hábitos saludables
            • Guiar en situaciones de primeros auxilios básicos

            Tu objetivo final es que el paciente se sienta escuchado, informado y más tranquilo después de hablar contigo, sabiendo que cuenta con el apoyo del equipo médico de la clínica para cualquier necesidad de salud.
            """
        
        # Creamos el prompt para la conversación
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("human", "{input}")
        ])
        
        # Crear la cadena de conversación
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        # Historial de mensajes
        self.conversation_history = []

    def ask(self, question):
        """Procesa una pregunta del usuario y devuelve la respuesta"""
        try:
            # Añadir contexto de conversaciones anteriores si existen
            response = self.chain.invoke({"input": question})
            
            # Guardar la conversación
            self.conversation_history.append(HumanMessage(content=question))
            self.conversation_history.append(AIMessage(content=response))
            
            return response
        except Exception as e:
            return f"Lo siento, tuve un problema para procesar tu pregunta. Error: {str(e)}"
    
    def reset_conversation(self):
        """Reinicia la conversación eliminando la memoria"""
        self.conversation_history = []
        return "Conversación reiniciada."

# Instancias globales para cada proveedor
openai_assistant = MedicalAssistant("openai")
groq_assistant = MedicalAssistant("groq")

# Asistente actual (por defecto OpenAI)
current_assistant = openai_assistant

def get_medical_response(question, provider=None):
    """Función para obtener respuesta del asistente médico virtual"""
    global current_assistant
    
    # Cambiar el asistente si se solicita un proveedor específico
    if provider == "groq":
        current_assistant = groq_assistant
    elif provider == "openai":
        current_assistant = openai_assistant
    
    return current_assistant.ask(question)

def reset_assistant(provider=None):
    """Función para reiniciar el asistente médico virtual"""
    global current_assistant
    
    # Cambiar el asistente si se solicita un proveedor específico
    if provider == "groq":
        current_assistant = groq_assistant
    elif provider == "openai":
        current_assistant = openai_assistant
    
    return current_assistant.reset_conversation()

def change_provider(provider):
    """Función para cambiar el proveedor del asistente"""
    global current_assistant
    
    if provider == "groq":
        current_assistant = groq_assistant
    else:
        current_assistant = openai_assistant
    
    return f"Proveedor cambiado a {provider.upper()}"