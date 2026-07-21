import datetime
import html
import requests
from reportlab.lib.pagesizes import letter
from scraping_casas import buscar_inmuebles_del_dia, scraping_casas
from dotenv import load_dotenv

from scraping_casas_pde import buscar_inmuebles_del_dia_pde
from scraping_terrenos import buscar_terrenos_del_dia

load_dotenv()

if __name__ == "__main__":
    buscar_inmuebles_del_dia()
    buscar_terrenos_del_dia()
    buscar_inmuebles_del_dia_pde()
