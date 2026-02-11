from playwright.async_api import async_playwright
from playwright_stealth import stealth_sync
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
        browser = None
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Ocultar automatización
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Navegar a la URL
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Esperar a que cargue el contenido
            await page.wait_for_timeout(3000)
            
            # Verificar si existe contenido (si no hay proforma registrada, no habrá datos)
            # Ajusta estos selectores según la estructura real de la página
            contenido = await page.content()
            
            # Si la página dice "no se encontró" o similar, retornar None
            if "no se encontr" in contenido.lower() or "sin datos" in contenido.lower():
                await browser.close()
                return None
            
            # Extraer datos del proveedor
            datos = {}
            
            try:
                # RUC - buscar por texto que contenga "RUC:"
                ruc_elements = await page.query_selector_all('text=/RUC/i')
                for elem in ruc_elements:
                    text = await elem.text_content()
                    if text and ':' in text:
                        datos['ruc'] = text.split(':')[-1].strip()
                        break
                
                # Razón Social / Nombre
                nombre_elements = await page.query_selector_all('text=/Razón Social|Nombre/i')
                for elem in nombre_elements:
                    text = await elem.text_content()
                    if text and ':' in text:
                        datos['nombre_proveedor'] = text.split(':')[-1].strip()
                        break
                
                # Buscar tablas con datos
                tablas = await page.query_selector_all('table')
                for tabla in tablas:
                    # Extraer texto de la tabla
                    tabla_texto = await tabla.inner_text()
                    
                    # Buscar descripción/objeto
                    if 'descripci' in tabla_texto.lower() or 'producto' in tabla_texto.lower():
                        filas = await tabla.query_selector_all('tr')
                        if len(filas) > 1:
                            for fila in filas[1:]:  # Saltar header
                                celdas = await fila.query_selector_all('td')
                                if len(celdas) > 2:
                                    desc = await celdas[2].text_content()
                                    if desc and len(desc.strip()) > 5:
                                        datos['objeto'] = desc.strip()
                                        break
                    
                    # Buscar valor total
                    if 'total' in tabla_texto.lower() or 'valor' in tabla_texto.lower():
                        import re
                        # Buscar patrón de números con decimales
                        valores = re.findall(r'[\d,]+\.[\d]+', tabla_texto)
                        if valores:
                            # Tomar el último valor (generalmente es el total)
                            valor_str = valores[-1].replace(',', '')
                            try:
                                datos['valor_total'] = float(valor_str)
                            except:
                                pass
                
                # Si no encontramos valor en tablas, buscar en todo el contenido
                if 'valor_total' not in datos:
                    import re
                    # Buscar "TOTAL:" seguido de número
                    total_match = re.search(r'TOTAL[:\s]+USD[\s]*([\d,]+\.[\d]+)', contenido, re.IGNORECASE)
                    if total_match:
                        valor_str = total_match.group(1).replace(',', '')
                        try:
                            datos['valor_total'] = float(valor_str)
                        except:
                            pass
                
            except Exception as e:
                print(f"Error extrayendo datos: {str(e)}")
            
            await browser.close()
            
            # Solo retornar datos si encontramos al menos el RUC o nombre
            if datos.get('ruc') or datos.get('nombre_proveedor'):
                return datos
            else:
                return None
            
        except Exception as e:
            print(f"Error scraping {ruc}: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            raise e