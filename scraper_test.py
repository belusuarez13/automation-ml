import datetime
import requests
from reportlab.lib.pagesizes import letter
from scraping_ml import scraping_ml
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from dotenv import load_dotenv
import os
import re
import time
from google import genai

load_dotenv()

def formatear_texto_para_reportlab(texto_markdown):
    """Convierte Markdown básico a bloques legibles para ReportLab."""
    if not texto_markdown:
        return []

    elementos = []
    for linea in texto_markdown.replace("\r\n", "\n").split("\n"):
        texto = linea.strip()
        if not texto:
            elementos.append(("spacer", ""))
            continue

        if re.match(r"^#{1,3}\s+", texto):
            nivel = len(texto) - len(texto.lstrip("#"))
            contenido = re.sub(r"^#{1,3}\s*", "", texto)
            contenido = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", contenido)
            contenido = re.sub(r"\*(.*?)\*", r"<i>\1</i>", contenido)
            elementos.append(("heading", (nivel, contenido)))
            continue

        if re.match(r"^[-*]\s+", texto):
            contenido = re.sub(r"^[-*]\s+", "", texto)
            contenido = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", contenido)
            contenido = re.sub(r"\*(.*?)\*", r"<i>\1</i>", contenido)
            elementos.append(("bullet", contenido))
            continue

        if re.match(r"^\d+\.\s+", texto):
            contenido = re.sub(r"^\d+\.\s+", "", texto)
            contenido = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", contenido)
            contenido = re.sub(r"\*(.*?)\*", r"<i>\1</i>", contenido)
            elementos.append(("number", contenido))
            continue

        contenido = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", texto)
        contenido = re.sub(r"\*(.*?)\*", r"<i>\1</i>", contenido)
        elementos.append(("paragraph", contenido))

    return elementos

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

def enviar_pdf_telegram(path_al_pdf, resumen_texto=""):
    time.sleep(10)
    if not os.path.exists(path_al_pdf):
        print(f"❌ Error: El archivo {path_al_pdf} no existe.")
        return

    # Nuevas variables seguras
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Faltan las variables de Telegram.")
        return

    # Endpoint nativo de Telegram para enviar archivos físicos
    urlPDF = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": '🤖 ¡Hola! Tu reporte diario está listo y adjunto aquí mismo con algunas recomendaciones.', # Texto que acompaña al PDF
        "parse_mode": "Markdown"  # Permite usar negritas con asteriscos
    }

    with open(path_al_pdf, 'rb') as f:
        files = {'document': f}
        try:
            response = requests.post(urlPDF, data=payload, files=files)
            if response.status_code == 200:
                print("✅ ¡PDF enviado con éxito a Telegram de forma gratuita!")
            else:
                print(f"❌ Error de Telegram: {response.text}")
        except Exception as e:
            print(f"💥 Falló la conexión con Telegram: {e}")

# Llama a esta función al final de tu script en lugar de la de WhatsApp:
# enviar_pdf_telegram("datos_2026-06-29.pdf", "📊 *Reporte Inmobiliario de Hoy*")

def buscar_inmuebles_del_dia():

    load_dotenv() 

    # url = "https://dogapi.dog/api/v2/breeds"
    
    # try:
    #     response = requests.get(url)
    #     response.raise_for_status()
    #     data = response.json()
    #     results = data.get("data", [])
    # except Exception as e:
    #     print(f"Error al conectar con la API: {e}")

    results = scraping_ml()


    #Resumir los datos con la IA
    ai_summary = analizar_datos_con_ia(results)

    # Obtener la fecha de hoy en formato AAAA-MM-DD
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    archivo_pdf = f"analisis_inmobiliario_{hoy_str}.pdf"
    
    doc = SimpleDocTemplate(archivo_pdf, pagesize=letter)
    styles = getSampleStyleSheet()

    estilo_ia = ParagraphStyle(
        'TextoIA',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        spaceAfter=6
    )

    estilo_heading1 = ParagraphStyle(
        'Heading1IA',
        parent=styles['Heading1'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1f4e79'),
        spaceBefore=8,
        spaceAfter=6
    )

    estilo_heading2 = ParagraphStyle(
        'Heading2IA',
        parent=styles['Heading2'],
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor('#2b5d8a'),
        spaceBefore=8,
        spaceAfter=4
    )

    estilo_heading3 = ParagraphStyle(
        'Heading3IA',
        parent=styles['Heading3'],
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#3c5a6b'),
        spaceBefore=6,
        spaceAfter=4
    )

    estilo_bullet = ParagraphStyle(
        'BulletIA',
        parent=estilo_ia,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=4
    )
    
    estilo_celda = ParagraphStyle(
        'CeldaTabla',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )
    
    story = []

    story.append(Paragraph("<b>Reporte de Mercado con Agente IA</b>", styles['Title']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>🧠 Conclusiones y Decisiones del Agente:</b>", styles['Heading2']))
    story.append(Spacer(1, 10))
    

    for bloque in formatear_texto_para_reportlab(ai_summary):
        tipo, valor = bloque
        if tipo == 'spacer':
            story.append(Spacer(1, 6))
        elif tipo == 'heading':
            nivel, contenido = valor
            if nivel == 1:
                story.append(Paragraph(contenido, estilo_heading1))
            elif nivel == 2:
                story.append(Paragraph(contenido, estilo_heading2))
            else:
                story.append(Paragraph(contenido, estilo_heading3))
        elif tipo == 'bullet':
            story.append(Paragraph(f"• {valor}", estilo_bullet))
        elif tipo == 'number':
            story.append(Paragraph(f"{valor}", estilo_ia))
        else:
            story.append(Paragraph(valor, estilo_ia))

    # 4. Separador antes de la tabla de datos
    story.append(Spacer(1, 25))
    story.append(Paragraph("<b>📊 Listado Completo de Propiedades:</b>", styles['Heading2']))
    story.append(Spacer(1, 10))

    
    def truncar_texto(texto, max_len=40):
        texto = str(texto or "")
        return texto if len(texto) <= max_len else texto[:max_len - 3] + "..."

    datos_tabla = [["Título", "Precio", "Ubicación", "Link"]] 
    for p in results:
        link = p.get('link', '') or 'Sin link'
        datos_tabla.append([
            truncar_texto(p.get('titulo', 'Sin título'), 35),
            truncar_texto(p.get('precio', 'Consultar'), 20),
            truncar_texto(p.get('direccion', 'No especificada'), 35),
            Paragraph(f"<a href=\"{link}\" color=\"blue\">link</a>", estilo_celda)
        ])
    
    # Construcción estética de la tabla con ReportLab
    tabla_propiedades = Table(datos_tabla, colWidths=[220, 90, 150, 60])
    tabla_propiedades.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f4f4f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    
    # Insertamos la tabla al final del mismo flujo ('story')
    story.append(tabla_propiedades)
    doc.build(story)

    enviar_pdf_telegram(archivo_pdf)

    print(f"Proceso terminado. {archivo_pdf}")

if __name__ == "__main__":
    buscar_inmuebles_del_dia()
