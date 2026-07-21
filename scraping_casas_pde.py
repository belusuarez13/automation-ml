import os
import time
from google import genai
import requests
from reportlab.lib.pagesizes import letter


from shared import HEADERS, crear_archivo, enviar_pdf_telegram, extraer_propiedades_infocasas
# URL de Apartamentos en Montevideo (Uruguay)
URL = "https://www.infocasas.com.uy/venta/apartamentos/maldonado/punta-del-este/2-o-mas-dormitorios/baratos/publicado-ayer"

def scraping_casas_pde(guardar=False, nombre_archivo="casas_pde.json"):
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
        descripcion = p.get('descripcion') or p.get('description') or ""
        datos_comprimidos += (
            f"Título: {p.get('titulo')}, "
            f"Precio: {p.get('precio')}, "
            f"Ubicación: {p.get('direccion')}, "
            f"Superficie: {p.get('superficie_m2')}, "
            f"Cuartos: {p.get('cuartos')}, "
            f"Descripción: {descripcion}, "
            f"Link: {p.get('link')}\n"
        )

    instrucciones = (
        "Eres un Agente de Inteligencia Artificial experto en inversión inmobiliaria en Punta del Este y mercados turísticos de alto standing. "
        "Tu objetivo es analizar la lista de apartamentos en venta desde la perspectiva de un inversor y no como comprador residencial. "
        "Prioriza propiedades con alto potencial de renta, reventa y posicionamiento premium.\n"
        "Da preferencia a apartamentos que tengan características como:\n"
        "1. Vista al mar o cercanía directa a la playa.\n"
        "2. Primera línea de playa o ubicación estratégica frente al mar.\n"
        "3. Piscina, amenities premium o valor de posicionamiento turístico.\n"
        "4. Precio atractivo por metro cuadrado frente a la competencia.\n\n"
        "Descarta publicaciones sospechosas, duplicadas o poco claras. Destaca estrictamente las 5 mejores 'Oportunidades de Inversión' del día. "
        "Para cada oportunidad elegida, justifica por qué esa propiedad tiene potencial de alquiler de alto standing, reventa premium o captación turística. "
        "Termina siempre con una sección llamada '🚀 Decisión Estratégica del Agente' donde indiques si hoy conviene comprar, esperar o negociar agresivamente."
    )

    prompt = (
        f"Analiza con mentalidad de inversionista premium y de mercado turístico las siguientes oportunidades detectadas hoy por el scraper:\n\n{datos_comprimidos}\n\n"
        "Filtra y sugiere especialmente los apartamentos que tengan vista al mar, primera línea de playa o piscina. "
        "Genera un reporte estructurado y profesional usando formato Markdown para leer en Telegram. "
        "Usa emojis financieros y de lujo (💰, 🌊, 🏖️, 🏊, 📈) para destacar los puntos clave."
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

def buscar_inmuebles_del_dia_pde():
    results = scraping_casas_pde()

    ai_summary = analizar_datos_con_ia(results)

    archivo_pdf = crear_archivo(title="aptos_pde", ai_summary=ai_summary, results=results)

    enviar_pdf_telegram(archivo_pdf)

    print(f"Proceso terminado. {archivo_pdf}")
