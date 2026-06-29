import datetime
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
    print(f"Proceso terminado. {archivo_pdf}")

if __name__ == "__main__":
    buscar_inmuebles_del_dia()
