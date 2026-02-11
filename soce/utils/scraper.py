from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from typing import Optional, Dict
import re

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scrape data from compraspublicas.gob.ec
    """
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={proceso_id}&ruc={ruc}"
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            page = await browser.new_page()
            
            # Navegar con timeout más corto
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            except PlaywrightTimeout:
                print(f"Timeout loading page for RUC {ruc}")
                await browser.close()
                return None
            
            # Esperar un momento para que cargue
            await page.wait_for_timeout(2000)
            
            # Obtener todo el contenido
            contenido = await page.content()
            texto = await page.inner_text('body')
            
            # Verificar si no hay datos
            if any(palabra in texto.lower() for palabra in ['no se encontr', 'sin datos', 'no existe', 'no registra']):
                await browser.close()
                return None
            
            datos = {}
            
            # Extraer RUC
            ruc_match = re.search(r'RUC[:\s]+(\d+)', texto, re.IGNORECASE)
            if ruc_match:
                datos['ruc'] = ruc_match.group(1)
            
            # Extraer nombre/razón social
            nombre_match = re.search(r'(?:Razón Social|Nombre)[:\s]+([^\n]+)', texto, re.IGNORECASE)
            if nombre_match:
                datos['nombre_proveedor'] = nombre_match.group(1).strip()
            
            # Extraer valor total (buscar USD seguido de número)
            valor_match = re.search(r'TOTAL[:\s]+(?:USD\.?)?[\s]*([\d,]+\.?\d*)', texto, re.IGNORECASE)
            if valor_match:
                valor_str = valor_match.group(1).replace(',', '')
                try:
                    datos['valor_total'] = float(valor_str)
                except ValueError:
                    pass
            
            # Buscar descripción en tablas
            tablas = await page.query_selector_all('table')
            for tabla in tablas:
                filas = await tabla.query_selector_all('tr')
                for fila in filas:
                    celdas = await fila.query_selector_all('td')
                    if len(celdas) >= 3:
                        texto_celda = await celdas[2].text_content()
                        if texto_celda and len(texto_celda.strip()) > 10:
                            datos['objeto'] = texto_celda.strip()[:500]  # Limitar longitud
                            break
                if 'objeto' in datos:
                    break
            
            await browser.close()
            
            # Solo retornar si encontramos datos útiles
            if datos.get('ruc') or datos.get('valor_total'):
                return datos
            
            return None
            
    except Exception as e:
        print(f"Error scraping RUC {ruc}: {str(e)}")
        if browser:
            try:
                await browser.close()
            except:
                pass
        return None