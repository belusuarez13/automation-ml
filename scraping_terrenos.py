import json
import os
import time
from urllib.parse import urljoin
from google import genai
from reportlab.lib.pagesizes import letter
import requests
from bs4 import BeautifulSoup

from shared import HEADERS, crear_archivo, enviar_pdf_telegram, extraer_propiedades_infocasas

# URL de Apartamentos en Montevideo (Uruguay)
URL = "https://www.infocasas.com.uy/venta/terrenos/"
FILTROS_COMUNES = "/baratos/publicado-ayer"
DEPARTAMENTOS = ["maldonado", "canelones", "montevideo"]

def scraping_terrenos(guardar=False, nombre_archivo="terrenos.json"):
    try:
        items = []
        for departamento in DEPARTAMENTOS:
            url_departamento = f"{URL}{departamento}{FILTROS_COMUNES}"
            response = requests.get(url_departamento, headers=HEADERS, timeout=20)
            response.raise_for_status()

            newItems = extraer_propiedades_infocasas(response.text)

            if not newItems:
                print(f"No se encontraron terrenos en {departamento}: no se pudo extraer la lista desde el JSON del sitio.")
                continue

            items.extend(newItems)

            print(f"Se encontraron {len(newItems)} terrenos en {departamento} y {len(items)} acumulados hasta ahora.\n")

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
        datos_comprimidos += f"Título: {p.get('titulo')}, Precio: {p.get('precio')}, Ubicación: {p.get('direccion')}, Link: {p.get('link')}\n"

    # --- INSTRUCCIONES ENFOCADAS EN ANÁLISIS POR ZONAS Y OPORTUNIDADES DE TERRENOS ---
    instrucciones = (
        "Eres un Agente de Inteligencia Artificial experto en inversión inmobiliaria, desarrollo de terrenos y valorización de zonas. "
        "Tu objetivo es analizar la lista de terrenos en venta desde la perspectiva de un inversor estratégico, no de un comprador residencial. "
        "Evalúa cada oportunidad en función de su potencial de compra, desarrollo futuro, revalorización y venta posterior.\n"
        "Prioriza terrenos que tengan ventajas en:\n"
        "1. Ubicación estratégica y crecimiento futuro de la zona.\n"
        "2. Accesibilidad, infraestructura, servicios y proyección urbanística.\n"
        "3. Potencial de valorización, subdivisión, desarrollo o venta en el mediano plazo.\n"
        "4. Precio por metro cuadrado atractivo frente al entorno y la tendencia del mercado.\n\n"
        "Descarta publicaciones sospechosas, duplicadas, poco claras o claramente sobrevaloradas. Destaca estrictamente las 5 mejores 'Oportunidades de Inversión' del día. "
        "Para cada oportunidad elegida, justifica financieramente tu decisión explicando por qué esa zona tiene potencial de crecimiento, por qué el precio parece atractivo y qué tipo de estrategia de venta o desarrollo podría generar valor futuro. "
        "Termina siempre con una sección llamada '🚀 Decisión Estratégica del Agente' donde indiques si hoy conviene comprar, esperar, negociar con agresividad o mantener liquidez para nuevas oportunidades."
    )

    prompt = (
        f"Analiza con mentalidad de inversionista de terrenos y desarrollo inmobiliario las siguientes oportunidades detectadas hoy por el scraper:\n\n{datos_comprimidos}\n\n"
        "Haz un análisis por zonas, identificando cuáles tienen mejor potencial de valorización, crecimiento y salida futura. "
        "Genera un reporte estructurado y profesional usando formato Markdown para leer en Telegram. "
        "Usa emojis financieros y de estrategia (💰, 📈, 🏗️, 🌍, 🧭) para destacar los puntos clave."
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

def buscar_terrenos_del_dia():
    results = scraping_terrenos()

    ai_summary = analizar_datos_con_ia(results)

    archivo_pdf = crear_archivo(title="terrenos", ai_summary=ai_summary, results=results)

    enviar_pdf_telegram(archivo_pdf)

    print(f"Proceso terminado. {archivo_pdf}")