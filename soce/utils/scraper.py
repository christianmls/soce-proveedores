from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> List[Dict]:
    """
    Captura cada fila de la tabla de productos (1-7) y detecta archivos anexos.
    """
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    lista_items = []
    browser = None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except PlaywrightTimeout:
                await browser.close()
                return []
            
            await page.wait_for_timeout(3000)
            texto_completo = await page.inner_text('body')
            
            # Datos base del proveedor (Cabecera)
            datos_base = {'ruc': ruc, 'tiene_archivos': False}
            patterns = {
                'razon_social': r'Razón Social[:\s]+([^\n]+)',
                'correo_electronico': r'Correo electrónico[:\s]+([^\s\n]+@[^\s\n]+)',
                'ubicacion': r'Cantón[:\s]+([^\n]+)',
                'direccion': r'Dirección[:\s]+([^\n]+)'
            }
            
            for key, pat in patterns.items():
                match = re.search(pat, texto_completo, re.IGNORECASE)
                if match:
                    datos_base[key] = match.group(1).strip()

            def clean_float(txt):
                if not txt: return 0.0
                clean = re.sub(r'[^\d\.]', '', txt.replace(',', '')) 
                try:
                    return float(clean)
                except:
                    return 0.0

            # DETECCIÓN DE ARCHIVOS (Iconos de descarga)
            botones = await page.query_selector_all("input[type='image'], img[src*='descargar'], img[src*='download']")
            datos_base['tiene_archivos'] = len(botones) > 0

            # EXTRACCIÓN DE FILAS (Columnas 1 a 7)
            tablas = await page.query_selector_all('table')
            for tabla in tablas:
                header = await tabla.inner_text()
                if not ("descripci" in header.lower() and "cantidad" in header.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                for fila in filas:
                    celdas = await fila.query_selector_all('td')
                    texto = await fila.inner_text()
                    
                    # Saltar encabezados y fila de TOTAL
                    if "descripci" in texto.lower() or "TOTAL:" in texto or len(celdas) < 7:
                        continue

                    try:
                        # Mapeo: [0]No [1]CPC [2]Desc [3]Unidad [4]Cant [5]V.Unit [6]V.Tot
                        item = datos_base.copy()
                        item['descripcion_producto'] = (await celdas[2].inner_text()).strip()
                        item['unidad'] = (await celdas[3].inner_text()).strip()
                        item['cantidad'] = clean_float(await celdas[4].inner_text())
                        item['valor_unitario'] = clean_float(await celdas[5].inner_text())
                        item['valor_total'] = clean_float(await celdas[6].inner_text())
                        lista_items.append(item)
                    except:
                        continue
                break # Solo procesamos la tabla de productos principal
            
            await browser.close()
            return lista_items

    except Exception as e:
        if browser: await browser.close()
        return []