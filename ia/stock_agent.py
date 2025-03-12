from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from .models import Medicamento, MovimientoStock
from django.utils import timezone
from django.db.models import Sum, Count, F, Value, IntegerField
from django.db.models.functions import ExtractMonth
import datetime
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class StockAnalysisAgent:
    def __init__(self, provider="groq"):
        """Inicializa el agente de análisis de stock"""
        self.provider = provider
        
        try:
            if self.provider == "groq" and os.getenv("GROQ_API_KEY"):
                # Configuración para Groq
                api_key = os.getenv("GROQ_API_KEY")
                base_url = "https://api.groq.com/openai/v1"
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    model_name="mixtral-8x7b-32768"
                )
            else:
                # Configuración para OpenAI como respaldo
                api_key = os.getenv("OPENAI_API_KEY")
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    model_name="gpt-3.5-turbo"
                )
            
            # Mensaje del sistema para el análisis de stock
            self.system_message = """
            Eres un analista de inventario farmacéutico especializado en optimización de stock y análisis de patrones de consumo.
            
            Para cada conjunto de datos que analices, debes:
            1. Identificar medicamentos con stock bajo o crítico que requieren atención inmediata
            2. Detectar patrones en el consumo de medicamentos (tendencias, frecuencia, cantidades)
            3. Sugerir estrategias para optimizar el inventario y evitar agotamientos
            4. Proporcionar recomendaciones específicas basadas en los datos analizados
            
            Presenta toda la información de manera estructurada y fácil de entender para el personal de farmacia.
            """
            
            # Crear el prompt para el análisis
            self.stock_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_message),
                ("system", "A continuación se presentan los datos de stock de medicamentos para análisis:"),
                ("system", "{stock_data}"),
                ("human", "{query}")
            ])
            
            # Cadena de procesamiento
            self.stock_chain = self.stock_prompt | self.llm | StrOutputParser()
        
        except Exception as e:
            logger.error(f"Error inicializando StockAnalysisAgent: {str(e)}")
            raise
    
    def analyze_medication_stock(self, query_type):
        """Analiza el stock de medicamentos según el tipo de consulta"""
        try:
            query = ""
            stock_data = ""
            
            if query_type == "alertas_stock":
                try:
                    # Obtener medicamentos con stock bajo
                    medicamentos_bajos = Medicamento.objects.filter(
                        cantidad_actual__lte=F('cantidad_minima')
                    ).order_by('cantidad_actual')[:20]
                    
                    # Formatear datos para análisis
                    if medicamentos_bajos.exists():
                        stock_data = "MEDICAMENTOS CON STOCK BAJO:\n\n"
                        for med in medicamentos_bajos:
                            stock_data += f"Medicamento: {med.nombre} ({med.presentacion})\n"
                            stock_data += f"Stock actual: {med.cantidad_actual}\n"
                            stock_data += f"Stock mínimo: {med.cantidad_minima}\n"
                            stock_data += f"Laboratorio: {med.laboratorio.nombre}\n"
                            stock_data += f"Última reposición: {med.fecha_ultima_reposicion.strftime('%d/%m/%Y')}\n\n"
                    else:
                        stock_data = "No hay medicamentos con stock bajo actualmente."
                except Exception as e:
                    logger.error(f"Error en alertas_stock: {str(e)}")
                    stock_data = f"Error al obtener datos de stock bajo: {str(e)}"
                
                query = "Identifica los medicamentos que requieren reposición urgente. Prioriza la lista y sugiere cantidades a pedir basándote en los niveles de stock mínimo."
                
            elif query_type == "patrones_consumo":
                try:
                    # Obtener movimientos de los últimos 3 meses (salidas)
                    tres_meses = timezone.now() - datetime.timedelta(days=90)
                    movimientos = MovimientoStock.objects.filter(
                        fecha__gte=tres_meses,
                        tipo='salida'
                    ).values('medicamento__nombre').annotate(
                        total=Sum('cantidad'),
                        frecuencia=Count('id')
                    ).order_by('-total')[:30]
                    
                    # Formatear datos para análisis
                    if movimientos:
                        stock_data = "PATRONES DE CONSUMO (ÚLTIMOS 3 MESES):\n\n"
                        for mov in movimientos:
                            stock_data += f"Medicamento: {mov['medicamento__nombre']}\n"
                            stock_data += f"Consumo total: {mov['total']} unidades\n"
                            stock_data += f"Frecuencia de solicitud: {mov['frecuencia']} veces\n\n"
                    else:
                        stock_data = "No hay datos de consumo registrados en los últimos 3 meses."
                except Exception as e:
                    logger.error(f"Error en patrones_consumo: {str(e)}")
                    stock_data = f"Error al obtener datos de patrones de consumo: {str(e)}"
                
                query = "Analiza estos datos de consumo de medicamentos. Identifica patrones, medicamentos de alto consumo y tendencias. Sugiere estrategias para optimizar el inventario basadas en estos patrones."
                
            elif query_type == "estacionalidad":
                try:
                    # Usamos annotate con ExtractMonth en lugar de extra para mejor compatibilidad
                    movimientos = MovimientoStock.objects.filter(
                        tipo='salida'
                    ).annotate(
                        month=ExtractMonth('fecha')
                    ).values('month', 'medicamento__nombre').annotate(
                        total=Sum('cantidad')
                    ).order_by('month', '-total')[:50]
                    
                    # Formatear datos para análisis
                    meses = {
                        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                    }
                    
                    if movimientos:
                        stock_data = "ANÁLISIS DE ESTACIONALIDAD:\n\n"
                        current_month = None
                        
                        for mov in movimientos:
                            month = int(mov['month'])
                            if current_month != month:
                                stock_data += f"\n--- {meses.get(month, 'Mes ' + str(month))} ---\n"
                                current_month = month
                                
                            stock_data += f"Medicamento: {mov['medicamento__nombre']}\n"
                            stock_data += f"Consumo: {mov['total']} unidades\n\n"
                    else:
                        stock_data = "No hay suficientes datos para realizar un análisis estacional."
                except Exception as e:
                    logger.error(f"Error en estacionalidad: {str(e)}")
                    stock_data = f"Error al obtener datos de estacionalidad: {str(e)}"
                
                query = "Analiza estos datos de consumo por mes. Identifica patrones estacionales y medicamentos cuyo consumo varía según la época del año. Sugiere estrategias de abastecimiento considerando estos factores estacionales."
            
            else:
                return "Tipo de análisis no válido."
            
            # Realizar análisis
            if not stock_data:
                return "No hay datos suficientes para realizar este análisis."
            
            # Intentar hacer el análisis con el LLM
            try:    
                analysis = self.stock_chain.invoke({
                    "stock_data": stock_data,
                    "query": query
                })
                return analysis
            except Exception as e:
                logger.error(f"Error al invocar LLM: {str(e)}")
                # Si falla el LLM, devolver al menos los datos recopilados
                return f"Error al generar análisis automático, pero se han recopilado los siguientes datos:\n\n{stock_data}"
            
        except Exception as e:
            logger.error(f"Error general en analyze_medication_stock: {str(e)}")
            return f"Error al analizar stock de medicamentos: {str(e)}"

# Instancia global del agente
# Usamos una función para asegurar que se crea solo cuando se necesita
_stock_agent_instance = None

def get_stock_agent():
    global _stock_agent_instance
    if _stock_agent_instance is None:
        try:
            _stock_agent_instance = StockAnalysisAgent()
        except Exception as e:
            logger.error(f"Error al crear instancia de StockAnalysisAgent: {str(e)}")
            # Crear una instancia fallback con funcionalidad mínima
            class FallbackAgent:
                def analyze_medication_stock(self, _):
                    return "El servicio de análisis de stock no está disponible en este momento."
            _stock_agent_instance = FallbackAgent()
    return _stock_agent_instance

def analyze_medication_stock(query_type):
    """Función para analizar stock de medicamentos"""
    agent = get_stock_agent()
    return agent.analyze_medication_stock(query_type)