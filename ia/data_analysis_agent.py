import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from clinicas.models import Paciente, HistorialMedico, Consulta

load_dotenv()

class DataAnalysisAgent:
    def __init__(self, provider="groq"):
        """Inicializa el agente de análisis de datos médicos"""
        self.provider = provider
        
        if self.provider == "groq" and os.getenv("GROQ_API_KEY"):
            # Configuración para Groq
            api_key = os.getenv("GROQ_API_KEY")
            base_url = "https://api.groq.com/openai/v1"
            self.llm = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model_name="mixtral-8x7b-32768"  # Usando mixtral para análisis de datos
            )
        else:
            # Configuración para OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                api_key=api_key,
                model_name="gpt-3.5-turbo"
            )

        # Definir el sistema de instrucciones para el agente de análisis
        self.system_message = """
        Eres un asistente de análisis médico especializado en identificar patrones y proporcionar insights 
        sobre datos médicos. Tu objetivo es ayudar a los profesionales médicos a obtener información 
        valiosa a partir de historiales médicos, consultas y diagnósticos.

        Para cada conjunto de datos que analices, debes:
        1. Identificar patrones recurrentes en los síntomas o diagnósticos
        2. Detectar posibles correlaciones entre diferentes factores médicos
        3. Sugerir áreas de seguimiento o investigación adicional
        4. Proporcionar un resumen claro y conciso de los hallazgos más importantes

        Recuerda que tus análisis son herramientas de apoyo para el personal médico, no diagnósticos definitivos.
        Siempre enfatiza la importancia del juicio clínico profesional y nunca sugieras cambios en tratamientos
        sin la supervisión médica adecuada.
        
        Presenta toda la información de manera estructurada y fácil de entender para profesionales médicos.
        """
        
        # Crear el prompt para el análisis
        self.patient_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("system", "A continuación se presentan los datos del paciente y su historial médico para análisis:"),
            ("system", "{patient_data}"),
            ("human", "Por favor, analiza esta información y proporciona insights relevantes.")
        ])
        
        # Cadena de procesamiento
        self.patient_chain = self.patient_prompt | self.llm | StrOutputParser()
        
        # Prompt para análisis general
        self.general_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("system", "A continuación se presentan datos generales de múltiples pacientes para análisis:"),
            ("system", "{general_data}"),
            ("human", "{query}")
        ])
        
        # Cadena para análisis general
        self.general_chain = self.general_prompt | self.llm | StrOutputParser()
        
    def analyze_patient(self, patient_id):
        """Analiza los datos médicos de un paciente específico"""
        try:
            # Obtener datos del paciente
            patient = Paciente.objects.get(id=patient_id)
            medical_history = HistorialMedico.objects.filter(paciente=patient)
            consultations = Consulta.objects.filter(paciente=patient)
            
            # Estructurar datos para análisis
            patient_data = {
                "nombre": f"{patient.nombre} {patient.paterno} {patient.materno}".strip(),
                "genero": "Masculino" if patient.genero == "M" else "Femenino",
                "fecha_nacimiento": patient.fecha_nacimiento.strftime("%Y-%m-%d"),
                "historiales": [
                    {
                        "fecha": h.fecha.strftime("%Y-%m-%d"),
                        "descripcion": h.descripcion,
                        "tratamiento": h.tratamiento,
                        "notas": h.notas
                    } for h in medical_history
                ],
                "consultas": [
                    {
                        "fecha": c.fecha.strftime("%Y-%m-%d %H:%M"),
                        "motivo": c.motivo,
                        "diagnostico": c.diagnostico,
                        "doctor": f"{c.doctor.nombre} {c.doctor.apellido} - {c.doctor.especialidad}"
                    } for c in consultations
                ]
            }
            
            # Convertir a formato texto para el prompt
            patient_data_text = f"""
            DATOS DEL PACIENTE:
            Nombre: {patient_data['nombre']}
            Género: {patient_data['genero']}
            Fecha de nacimiento: {patient_data['fecha_nacimiento']}
            
            HISTORIALES MÉDICOS:
            {self._format_medical_histories(patient_data['historiales'])}
            
            CONSULTAS MÉDICAS:
            {self._format_consultations(patient_data['consultas'])}
            """
            
            # Realizar análisis
            analysis = self.patient_chain.invoke({"patient_data": patient_data_text})
            return analysis
            
        except Paciente.DoesNotExist:
            return "Error: Paciente no encontrado."
        except Exception as e:
            return f"Error al analizar datos del paciente: {str(e)}"
    
    def analyze_general_data(self, query_type):
        """Realiza análisis generales sobre los datos médicos"""
        try:
            query = ""
            general_data = ""
            
            if query_type == "tendencias_sintomas":
                # Obtener los motivos de consulta más comunes
                consultas = Consulta.objects.all()[:50]  # Limitamos a 50 para eficiencia
                motivos = [c.motivo for c in consultas]
                
                general_data = "MOTIVOS DE CONSULTA RECIENTES:\n" + "\n".join(motivos)
                query = "Analiza estos motivos de consulta e identifica tendencias o patrones en los síntomas reportados."
                
            elif query_type == "eficacia_tratamientos":
                # Obtener historiales con tratamientos
                historiales = HistorialMedico.objects.filter(tratamiento__isnull=False)[:30]
                
                data_list = []
                for h in historiales:
                    data_list.append(f"Descripción: {h.descripcion}\nTratamiento: {h.tratamiento}\nNotas posteriores: {h.notas}")
                
                general_data = "TRATAMIENTOS Y RESULTADOS:\n" + "\n\n".join(data_list)
                query = "Analiza estos tratamientos y sus resultados. ¿Qué enfoques parecen ser más efectivos para qué tipos de condiciones?"
                
            elif query_type == "distribucion_genero_edad":
                # Análisis demográfico básico
                pacientes = Paciente.objects.all()[:100]
                
                gender_count = {"M": 0, "F": 0}
                age_groups = {"0-18": 0, "19-40": 0, "41-65": 0, "65+": 0}
                
                import datetime
                current_year = datetime.date.today().year
                
                for p in pacientes:
                    # Contar género
                    gender_count[p.genero] += 1
                    
                    # Calcular grupo de edad
                    birth_year = p.fecha_nacimiento.year
                    age = current_year - birth_year
                    
                    if age <= 18:
                        age_groups["0-18"] += 1
                    elif age <= 40:
                        age_groups["19-40"] += 1
                    elif age <= 65:
                        age_groups["41-65"] += 1
                    else:
                        age_groups["65+"] += 1
                
                general_data = f"""
                DISTRIBUCIÓN POR GÉNERO:
                Masculino: {gender_count['M']}
                Femenino: {gender_count['F']}
                
                DISTRIBUCIÓN POR EDAD:
                0-18 años: {age_groups['0-18']}
                19-40 años: {age_groups['19-40']}
                41-65 años: {age_groups['41-65']}
                65+ años: {age_groups['65+']}
                """
                
                query = "Analiza la distribución demográfica de pacientes por género y edad. ¿Qué grupos parecen requerir más atención médica y qué implicaciones podría tener esto para la clínica?"
            
            else:
                return "Tipo de análisis no válido."
            
            # Realizar análisis
            analysis = self.general_chain.invoke({
                "general_data": general_data,
                "query": query
            })
            
            return analysis
            
        except Exception as e:
            return f"Error al realizar análisis general: {str(e)}"
            
    def _format_medical_histories(self, histories):
        """Formatea historiales médicos para el prompt"""
        if not histories:
            return "No hay historiales médicos registrados."
            
        result = []
        for h in histories:
            entry = f"Fecha: {h['fecha']}\n"
            entry += f"Descripción: {h['descripcion']}\n"
            
            if h['tratamiento']:
                entry += f"Tratamiento: {h['tratamiento']}\n"
            if h['notas']:
                entry += f"Notas: {h['notas']}\n"
                
            result.append(entry)
            
        return "\n".join(result)
        
    def _format_consultations(self, consultations):
        """Formatea consultas médicas para el prompt"""
        if not consultations:
            return "No hay consultas médicas registradas."
            
        result = []
        for c in consultations:
            entry = f"Fecha: {c['fecha']}\n"
            entry += f"Doctor: {c['doctor']}\n"
            entry += f"Motivo: {c['motivo']}\n"
            
            if c['diagnostico']:
                entry += f"Diagnóstico: {c['diagnostico']}\n"
                
            result.append(entry)
            
        return "\n".join(result)

# Instancia global del agente de análisis
analysis_agent = DataAnalysisAgent()

def analyze_patient_data(patient_id):
    """Función para analizar los datos de un paciente específico"""
    return analysis_agent.analyze_patient(patient_id)

def analyze_general_medical_data(query_type):
    """Función para realizar análisis generales de datos médicos"""
    return analysis_agent.analyze_general_data(query_type)