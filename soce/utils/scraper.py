from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> List[Dict]:
    """
    Scraper Estricto Columna a Columna (1-7).
    Recupera CADA fila como un ítem independiente.
    """
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    lista_items = []
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except PlaywrightTimeout:
                print(f"Timeout cargando RUC {ruc}")
                await browser.close()
                return []
            
            await page.wait_for_timeout(3000)
            texto_completo = await page.inner_text('body')
            
            # --- 1. DATOS DEL PROVEEDOR ---
            datos_base = {'ruc': ruc}
            # (Aquí mantenemos tu lógica de regex que ya funcionaba bien para los datos de cabecera)
            patterns = {
                'razon_social': [r'Razón Social[:\s]+([^\n]+)', r'Nombre[:\s]+([^\n]+)'],
                'correo_electronico': [r'Correo electrónico[:\s]+([^\s\n]+@[^\s\n]+)'],
                'telefono': [r'Teléfono[:\s]+([\d\s\-\(\)]+)'],
                'pais': [r'País[:\s]+([^\n]+)'],
                'provincia': [r'Provincia[:\s]+([^\n]+)'],
                'canton': [r'Cantón[:\s]+([^\n]+)'],
                'direccion': [r'Dirección[:\s]+([^\n]+)']
            }
            
            for key, pat_list in patterns.items():
                for pat in pat_list:
                    match = re.search(pat, texto_completo, re.IGNORECASE)
                    if match:
                        datos_base[key] = match.group(1).strip()
                        break

            # Helper para limpiar dinero (quita USD y comas)
            def clean_float(txt):
                if not txt: return 0.0
                clean = re.sub(r'[^\d\.]', '', txt.replace(',', '')) 
                try:
                    return float(clean)
                except:
                    return 0.0

            # --- 2. DETECCIÓN DE ARCHIVOS (El disquete azul) ---
            tiene_archivos = False
            botones_descarga = await page.query_selector_all("input[type='image']")
            if len(botones_descarga) > 0:
                tiene_archivos = True
            else:
                imgs = await page.query_selector_all("img[src*='descargar'], img[src*='download']")
                if len(imgs) > 0: tiene_archivos = True
            
            datos_base['tiene_archivos'] = tiene_archivos

            # --- 3. EXTRACCIÓN FILA POR FILA (1 al 7) ---
            tablas = await page.query_selector_all('table')
            
            for tabla in tablas:
                header = await tabla.inner_text()
                # Confirmamos que es la tabla de productos
                if not ("descripci" in header.lower() and "cantidad" in header.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                
                for fila in filas:
                    celdas = await fila.query_selector_all('td')
                    texto_fila = await fila.inner_text()
                    
                    # Ignorar headers y fila de Total General
                    if "descripci" in texto_fila.lower() or "TOTAL:" in texto_fila:
                        continue

                    # Necesitamos al menos 7 columnas según tu requerimiento
                    # [0]No [1]CPC [2]Desc [3]Und [4]Cant [5]V.Unit [6]V.Tot
                    if len(celdas) >= 7:
                        try:
                            # Extraemos TEXTO de cada columna
                            txt_no = (await celdas[0].inner_text()).strip()   # Col 1
                            txt_cpc = (await celdas[1].inner_text()).strip()  # Col 2
                            txt_desc = (await celdas[2].inner_text()).strip() # Col 3
                            txt_und = (await celdas[3].inner_text()).strip()  # Col 4
                            txt_cant = (await celdas[4].inner_text()).strip() # Col 5
                            txt_vunit = (await celdas[5].inner_text()).strip() # Col 6
                            txt_vtotal = (await celdas[6].inner_text()).strip() # Col 7

                            # Validamos que 'Cantidad' parezca un número para confirmar que es fila de datos
                            if any(c.isdigit() for c in txt_cant):
                                item = datos_base.copy()
                                
                                # Concatenamos No. y CPC en la descripción para no perder el dato
                                item['descripcion_producto'] = f"#{txt_no} [CPC:{txt_cpc}] {txt_desc}"
                                item['unidad'] = txt_und
                                item['cantidad'] = clean_float(txt_cant)
                                item['valor_unitario'] = clean_float(txt_vunit)
                                item['valor_total'] = clean_float(txt_vtotal)
                                
                                lista_items.append(item)
                        
                        except Exception as e:
                            print(f"Error leyendo celda: {e}")
                            continue

                # Si ya sacamos datos de esta tabla, terminamos
                if len(lista_items) > 0:
                    break

            await browser.close()
            return lista_items

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return []