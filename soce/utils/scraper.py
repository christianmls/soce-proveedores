from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import asyncio
from typing import Optional, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scrape data from compraspublicas.gob.ec
    
    Args:
        proceso_id: ID del proceso (parámetro 'id' en la URL)
        ruc: RUC del proveedor
    
    Returns:
        Dict con los datos extraídos o None si no se encontró información
    """
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={proceso_id}&ruc={ruc}"
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Aplicar stealth
            await stealth_async(page)
            
            # Navegar a la URL
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Esperar a que cargue el contenido
            await page.wait_for_timeout(2000)
            
            # Verificar si existe contenido (si no hay proforma registrada, no habrá datos)
            datos_proveedor = await page.query_selector('.datos-proveedor, #datosProveedor, .panel')
            
            if not datos_proveedor:
                await browser.close()
                return None
            
            # Extraer datos del proveedor
            datos = {}
            
            # RUC
            ruc_elem = await page.query_selector('text=/RUC:/')
            if ruc_elem:
                ruc_text = await ruc_elem.inner_text()
                datos['ruc'] = ruc_text.split(':')[1].strip() if ':' in ruc_text else ruc
            
            # Razón Social / Nombre
            nombre_elem = await page.query_selector('text=/Razón Social:|Nombre:/')
            if nombre_elem:
                nombre_text = await nombre_elem.inner_text()
                datos['nombre_proveedor'] = nombre_text.split(':')[1].strip() if ':' in nombre_text else ""
            
            # Objeto del proceso / Descripción
            objeto_elem = await page.query_selector('text=/Descripción del Producto|Detalle del objeto/')
            if objeto_elem:
                # Buscar la tabla de productos
                tabla = await page.query_selector('table')
                if tabla:
                    filas = await tabla.query_selector_all('tr')
                    if len(filas) > 1:
                        celdas = await filas[1].query_selector_all('td')
                        if len(celdas) > 2:
                            datos['objeto'] = await celdas[2].inner_text()
            
            # Valor Total
            valor_elem = await page.query_selector('text=/TOTAL:|Valor Total/')
            if valor_elem:
                # Buscar el valor en la misma fila o siguiente
                parent = await valor_elem.evaluate_handle('el => el.parentElement')
                valor_text = await parent.inner_text()
                # Extraer número (quitar USD, comas, etc)
                import re
                valor_match = re.search(r'[\d,.]+', valor_text.replace('USD', '').replace('.', ''))
                if valor_match:
                    datos['valor_total'] = float(valor_match.group().replace(',', '.'))
            
            await browser.close()
            return datos if datos else None
            
        except Exception as e:
            print(f"Error scraping {ruc}: {str(e)}")
            try:
                await browser.close()
            except:
                pass
            raise e