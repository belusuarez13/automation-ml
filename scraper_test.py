import datetime
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import time

def enviar_pdf_directo_whatsapp(path_al_pdf, resumen_texto=""):
    time.sleep(30)
    # Verificar que el archivo realmente se generó en el disco
    if not os.path.exists(path_al_pdf):
        print(f"❌ Error: El archivo {path_al_pdf} no existe en el directorio.")
        return

    INSTANCE_ID = os.getenv("WHATSAPP_INSTANCE")
    TOKEN = os.getenv("WHATSAPP_TOKEN")
    TU_TELEFONO = os.getenv("MI_TELEFONO")
    
    # Endpoint de UltraMsg para enviar archivos multimedia/documentos
    url_api = f"https://api.ultramsg.com{INSTANCE_ID}/messages/document"

    # Los parámetros de texto van en el diccionario 'data'
    payload = {
        "token": TOKEN,
        "to": TU_TELEFONO,
        "filename": os.path.basename(path_al_pdf), # Nombre que verá el usuario en WhatsApp
        "caption": resumen_texto
    }
    
    # Abrimos el archivo local en modo lectura binaria ('rb')
    with open(path_al_pdf, 'rb') as f:
        # El archivo físico se envía en el diccionario 'files'
        files = {
            'document': f
        }
        
        try:
            # Quitamos el encabezado urlencoded, requests maneja el multipart automáticamente
            response = requests.post(url_api, data=payload, files=files)
            if response.status_code == 200:
                print(f"✅ PDF '{path_al_pdf}' enviado directamente a tu WhatsApp desde el disco local.")
            else:
                print(f"❌ Error de la API de WhatsApp: {response.text}")
        except Exception as e:
            print(f"💥 Falló la conexión con la API al subir el archivo: {e}")

# Llama a esta función al final de tu flujo principal de Python, justo abajo de donde generas tu PDF:
# nombre_del_pdf = "reporte_diario.pdf"
# ... tu código que genera el PDF aquí ...
# enviar_pdf_directo_whatsapp(nombre_del_pdf, "🤖 ¡Hola! Tu reporte inmobiliario de hoy se generó con éxito.")



def buscar_inmuebles_del_dia():
    url = "https://dogapi.dog/api/v2/breeds"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        results = data.get("data", [])
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return

    # Obtener la fecha de hoy en formato AAAA-MM-DD
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    archivo_pdf = f"datos_{hoy_str}.pdf"
    
    doc = SimpleDocTemplate(archivo_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    estilo_celda = ParagraphStyle(
        'CeldaTabla',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )
    
    story = []
    story.append(Paragraph(f"Razas Hoy: {hoy_str}", styles['Title']))
    story.append(Spacer(1, 15))
    
    # Estructura de la tabla
    tabla_datos = [["Nombre", "Descripcion"]]
    
    results = results[:10]

    for item in results:
        att = item.get("attributes")
        # Extraer campos
        name = Paragraph(att.get("name"), estilo_celda)
        desc = Paragraph(att.get("description"), estilo_celda)
        
        tabla_datos.append([name, desc])
    
    tabla = Table(tabla_datos, colWidths=[180, 180])
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#FFE600")), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'), 
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])
    tabla.setStyle(estilo_tabla)
    story.append(tabla)
    
    doc.build(story)
    enviar_pdf_directo_whatsapp(archivo_pdf, "🤖 ¡Hola! Tu reporte inmobiliario de hoy se generó con éxito.")
    print(f"Proceso terminado. {archivo_pdf}")

if __name__ == "__main__":
    buscar_inmuebles_del_dia()
