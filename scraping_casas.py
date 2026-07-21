import os
import time
from google import genai
import requests
from reportlab.lib.pagesizes import letter


from shared import HEADERS, crear_archivo, enviar_pdf_telegram, extraer_propiedades_infocasas
# URL de Apartamentos en Montevideo (Uruguay)
URL = "https://www.infocasas.com.uy/venta/casas-y-apartamentos-y-terrenos-y-chacras-o-campos/montevideo/baratos/publicado-ayer"

def scraping_casas(guardar=False, nombre_archivo="propiedades.json"):
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        response.raise_for_status()

        items = extraer_propiedades_infocasas(response.text)

        if not items:
            print("No se encontraron propiedades: no se pudo extraer la lista desde el JSON del sitio.")
            return []

        print(f"Se encontraron {len(items)} propiedades en esta página:\n")

        responsePage2 = requests.get(URL + "/pagina2", headers=HEADERS, timeout=20)
        itemsPage2 = extraer_propiedades_infocasas(responsePage2.text)
        items.extend(itemsPage2)

        return items

    except requests.RequestException as e:
        print(f"Ocurrió un error de red: {e}")
        return []
    except Exception as e:
        print(f"Ocurrió un error en el backend: {e}")
        return []

def analizar_datos_con_ia(lista_propiedades):
    """
    Recibe los datos crudos del scraper, se los envía a Gemini 2.5 Flash
    y devuelve un resumen ejecutivo con toma de decisiones.
    """
    # Inicializa el cliente leyendo automáticamente la variable GEMINI_API_KEY
    # que configuramos en los secretos de GitHub
    try:
        client = genai.Client()
    except Exception as e:
        print(f"❌ Error al inicializar el cliente de IA: {e}")
        return "No se pudo generar el análisis de IA hoy debido a un problema técnico."
    
    # Convertimos los datos de las propiedades a un formato de texto limpio para la IA
    datos_comprimidos = ""
    for p in lista_propiedades[:30]:  # Limitamos a las primeras 30 para optimizar el prompt
        datos_comprimidos += (
            f"Título: {p.get('titulo')}, "
            f"Precio: {p.get('precio')}, "
            f"Ubicación: {p.get('direccion')}, "
            f"Superficie: {p.get('superficie_m2')}, "
            f"Link: {p.get('link')}\n"
        )

    # --- NUEVAS INSTRUCCIONES ENFOCADAS EN INVERSIÓN Y NEGOCIOS ---
    instrucciones = (
        "Eres un Agente de Inteligencia Artificial experto en Fondos de Inversión Inmobiliaria y Real Estate Flipping. "
        "Tu único objetivo es analizar la lista de casas en venta desde la perspectiva de un INVERSOR, no de un comprador residencial. "
        "Buscas propiedades con alto potencial de rentabilidad, ya sea para:\n"
        "1. Alquiler tradicional (zonas de alta demanda estudiantil o corporativa).\n"
        "2. Alquiler temporal/Airbnb (zonas turísticas o céntricas).\n"
        "3. Refacción y reventa rápida (Flipping) si el precio está muy por debajo del mercado.\n\n"
        "Descarta publicaciones sospechosas, duplicadas o sobrevaloradas. Destaca estrictamente las 5 mejores 'Oportunidades de Negocio' del día. "
        "Para cada oportunidad elegida, debes justificar financieramente tu decisión (por qué esa zona es estratégica o por qué el precio por metro cuadrado parece un regalo). "
        "Termina siempre con una sección llamada '🚀 Decisión Estratégica del Agente' donde indiques si el mercado de hoy amerita mover capital de inmediato, negociar agresivamente a la baja o quedarse en liquidez esperando mejores ofertas."
    )

    prompt = (
        f"Analiza con mentalidad de tiburón financiero las siguientes casas en venta detectadas hoy por el scraper:\n\n{datos_comprimidos}\n\n"
        "Genera un reporte estructurado y profesional usando formato Markdown para leer en Telegram. "
        "Usa emojis financieros (💰, 📈, 🏢, 🛠️) para destacar los puntos clave."
    )

    try:
        print("🤖 El Agente de IA está buscando las mejores oportunidades...")
        response = client.models.generate_content(
            model='gemini-2.5-flash', # El modelo gratuito, rápido y potente de Google [5]
            contents=prompt,
            config={'system_instruction': instrucciones}
        )
        return response.text
    except Exception as e:
        print(f"❌ Error al conectar con el Agente de IA: {e}")
        return "No se pudo generar el análisis de IA hoy debido a un problema técnico."

def buscar_inmuebles_del_dia():
    results = scraping_casas()

    ai_summary = analizar_datos_con_ia(results)

    archivo_pdf = crear_archivo(title="analisis_inmobiliario", ai_summary=ai_summary, results=results)

    enviar_pdf_telegram(archivo_pdf)

    print(f"Proceso terminado. {archivo_pdf}")
