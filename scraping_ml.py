import json
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# URL de Apartamentos en Montevideo (Uruguay)
URL = "https://www.infocasas.com.uy/venta/casas-y-apartamentos-y-terrenos-y-chacras-o-campos/montevideo/baratos/publicado-ayer"

# CRITICAL: Define un User-Agent real para que no te detecten como un bot de inmediato
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-UY,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.infocasas.com.uy/"
}


def limpiar_texto(texto):
    return " ".join(texto.split()) if texto else ""


def extraer_propiedades_infocasas(html_texto):
    soup = BeautifulSoup(html_texto, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        return []

    try:
        data = json.loads(script_tag.string or "{}")
    except json.JSONDecodeError:
        return []

    page_props = data.get("props", {}).get("pageProps", {})
    fetch_result = page_props.get("fetchResult") or {}
    search_fast = fetch_result.get("searchFast") or {}
    propiedades = search_fast.get("data") or []

    items = []
    for item in propiedades:
        precio_info = item.get("price") or {}
        precio_obj = precio_info.get("amount")
        moneda = precio_info.get("currency", {}).get("name", "")
        precio_formateado = f"{moneda} {precio_obj:,.0f}".strip() if precio_obj is not None else "Consultar precio"

        link = item.get("link") or ""
        if link and not link.startswith("http"):
            link = urljoin("https://www.infocasas.com.uy", link)

        items.append({
            "titulo": limpiar_texto(item.get("title") or "Sin título"),
            "precio": precio_formateado,
            "link": link or "Sin link",
            "direccion": limpiar_texto(item.get("address") or "")
        })

    return items


def guardar_json(items, nombre_archivo="propiedades.json"):
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(items, archivo, ensure_ascii=False, indent=2)
    print(f"Se guardaron {len(items)} propiedades en {nombre_archivo}")


def scraping_ml(guardar=False, nombre_archivo="propiedades.json"):
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


def simular_scraping():
    return scraping_ml()


if __name__ == "__main__":
    scraping_ml()
