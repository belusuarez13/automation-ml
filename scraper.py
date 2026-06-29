import datetime
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def buscar_inmuebles_del_dia():
    url = "https://api.mercadolibre.com/sites/MLA/search"
    
    # Parámetros de búsqueda avanzados
    params = {
        "category": "MLA1459",    # Inmuebles
        "q": "Palermo CABA",      # Ubicación elegida
        "operation": "sale",      # FILTRO: Solo Ventas
        "sort": "newest",         # ORDEN: Los más nuevos primero
        "limit": 50               # Ampliamos el límite para revisar más publicaciones de hoy
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    except Exception as e:
        print(f"Error al conectar con la API de MercadoLibre: {e}")
        return

    # Obtener la fecha de hoy en formato AAAA-MM-DD
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    archivo_pdf = f"ventas_nuevas_{hoy_str}.pdf"
    
    doc = SimpleDocTemplate(archivo_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    estilo_celda = ParagraphStyle(
        'CeldaTabla',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )
    
    story = []
    story.append(Paragraph(f"Inmuebles en Venta Publicados Hoy: {hoy_str}", styles['Title']))
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"Ubicación: <b>{params['q']}</b> | Operación: <b>Venta</b>", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Estructura de la tabla
    tabla_datos = [["Título de la Propiedad", "Precio", "Ubicación", "Publicado", "Enlace"]]
    
    conteo_hoy = 0
    for item in results:
        # MercadoLibre devuelve date_created en formato ISO: "2026-06-24T14:32:01.000Z"
        date_created_raw = item.get("date_created", "")
        fecha_publicacion = date_created_raw.split("T")[0] if "T" in date_created_raw else ""
        
        # FILTRO DE PYTHON: Si no se publicó hoy, se salta (como vienen ordenadas, frena rápido)
        if fecha_publicacion != hoy_str:
            continue
            
        conteo_hoy += 1
        
        # Extraer campos
        titulo = Paragraph(item.get("title", "Sin título"), estilo_celda)
        
        moneda = item.get("currency_id", "ARS")
        precio_num = item.get("price", 0)
        precio = f"{moneda} {precio_num:,.0f}"
        
        address = item.get("address", {})
        ubicacion_txt = f"{address.get('city_name', '')}, {address.get('state_name', '')}"
        ubicacion = Paragraph(ubicacion_txt, estilo_celda)
        
        # Formatear la hora de publicación (opcional)
        hora = date_created_raw.split("T")[1][:5] if "T" in date_created_raw else ""
        publicado_txt = Paragraph(f"{fecha_publicacion} {hora}", estilo_celda)
        
        link_url = item.get("permalink", "#")
        link = Paragraph(f"<a href='{link_url}' color='blue'>Ver publicación</a>", estilo_celda)
        
        tabla_datos.append([titulo, precio, ubicacion, publicado_txt, link])
    
    # Validar si hubo publicaciones hoy
    if conteo_hoy == 0:
        story.append(Paragraph("No se encontraron propiedades nuevas publicadas en el día de hoy.", styles['Heading3']))
    else:
        # Anchos de columnas ajustados para 5 campos
        tabla = Table(tabla_datos, colWidths=[180, 80, 110, 80, 90])
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
    print(f"Proceso terminado. {conteo_hoy} propiedades encontradas hoy. Archivo guardado como: {archivo_pdf}")

if __name__ == "__main__":
    buscar_inmuebles_del_dia()
