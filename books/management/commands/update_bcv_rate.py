import logging
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.core.management.base import BaseCommand
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Ignorar la advertencia de certificado Inseguro que genera urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Command(BaseCommand):
    help = "Realiza Web Scraping contra la página oficial del Banco Central de Venezuela (BCV) para extraer y cachear la tasa oficial local."

    def handle(self, *args, **options):
        url = "https://www.bcv.org.ve/"
        self.stdout.write(f"Iniciando scraping de la fuente oficial: {url}...")

        try:
            # Los sitios de gobierno de Venezuela frecuentemente tienen certificados SSL vencidos/mal configurados.
            # verify=False permite conectar a pesar de esto.
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
                verify=False,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Error de red o certificado accediendo a {url}:\n{e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        
        # El arbolito actual del HTML del BCV: <div id="dolar"><div> ... <strong> 45,230000 </strong> ... </div></div>
        dolar_div = soup.find("div", id="dolar")
        if not dolar_div:
            self.stderr.write("Estructura no reconocida: No se encontró el div con id='dolar' en el DOM de la página del BCV.")
            return

        strong_tag = dolar_div.find("strong")
        if not strong_tag:
            self.stderr.write("Estructura no reconocida: No se encontró la etiqueta <strong> dentro de #dolar.")
            return

        rate_text_raw = strong_tag.text.strip()
        # Formatear el separador de decimales del formato europeo/latino (coma) al estandar (punto)
        rate_text = rate_text_raw.replace(",", ".")
        
        try:
            rate_decimal = Decimal(rate_text)
            
            # Guardamos la tasa en la misma key que el servicio get_exchange_rate_with_fallback revisa ("exchange_rate_usd_to_VES")
            cache_key = "exchange_rate_usd_to_VES"
            # Asignamos la caché de por vida (timeout=None) hasta la próxima vez que el cron ejecute este comando
            cache.set(cache_key, str(rate_decimal), timeout=None)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ CRON EXITOSO: La tasa oficial del BCV ha sido extraída y actualizada como fallback => {rate_decimal} VES/USD"
                )
            )
        except InvalidOperation as e:
            self.stderr.write(f"Error de casting transformando el texto de la tasa ('{rate_text}') a Decimal numérico:\n{e}")
