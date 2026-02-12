from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> List[Dict]:
    """
    Scraper ajustado para tablas con columna CPC (8 columnas).
    Recupera todas las filas y detecta archivos correctamente.
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
            
            await page.wait_for_timeout(3000) # Espera un poco más para asegurar la tabla
            texto_completo = await page.inner_text('body')
            
            # Validación básica
            if any(p in texto_completo.lower() for p in ['no se encontr', 'sin datos', 'no existe']):
                await browser.close()
                return []

            # --- 1. DATOS DEL PROVEEDOR ---
            datos_base = {'ruc': ruc}
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

            def clean_float(txt):
                if not txt: return 0.0
                # Elimina todo lo que no sea dígito o punto
                clean = re.sub(r'[^\d\.]', '', txt.replace(',', '')) 
                try:
                    return float(clean)
                except:
                    return 0.0

            # --- 2. DETECCIÓN DE ARCHIVOS (Corregido) ---
            # Buscamos específicamente inputs de tipo imagen (el disquete azul)
            # O celdas que tengan la imagen dentro
            tiene_archivos = False
            
            # Selector específico para el botón de descarga del SERCOP
            botones_descarga = await page.query_selector_all("input[type='image']")
            if len(botones_descarga) > 0:
                tiene_archivos = True
            else:
                # Intento alternativo por si cambia el HTML
                imgs_descarga = await page.query_selector_all("img[src*='disk'], img[src*='descargar'], img[src*='download']")
                if len(imgs_descarga) > 0:
                    tiene_archivos = True

            datos_base['tiene_archivos'] = tiene_archivos

            # --- 3. EXTRACCIÓN DE TABLA (Multi-Fila) ---
            tablas = await page.query_selector_all('table')
            
            gran_total = 0.0
            
            for tabla in tablas:
                header = await tabla.inner_text()
                # Buscamos la tabla correcta
                if not ("descripci" in header.lower() and "cantidad" in header.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                
                for fila in filas:
                    texto = await fila.inner_text()
                    celdas = await fila.query_selector_all('td')
                    
                    # A. Detectar TOTAL GENERAL (Fila inferior)
                    if "TOTAL:" in texto:
                        for celda in celdas:
                            txt = await celda.inner_text()
                            if any(c.isdigit() for c in txt) and "TOTAL" not in txt:
                                gran_total = clean_float(txt)
                        continue

                    # B. Detectar FILA DE PRODUCTO
                    # La tabla de tu imagen tiene 8 columnas:
                    # [0]No | [1]CPC | [2]Desc | [3]Und | [4]Cant | [5]V.Unit | [6]V.Tot | [7]USD
                    if len(celdas) >= 7 and "descripci" not in texto.lower():
                        try:
                            # Índices basados en tu imagen (0-based)
                            idx_desc = 2
                            idx_und = 3
                            idx_cant = 4
                            idx_vunit = 5
                            idx_vtotal = 6
                            
                            # Ajuste por si falta la columna CPC (a veces pasa)
                            if len(celdas) == 7: # Si faltara una columna
                                idx_desc = 1
                                idx_und = 2
                                idx_cant = 3
                                idx_vunit = 4
                                idx_vtotal = 5

                            txt_desc = (await celdas[idx_desc].inner_text()).strip()
                            txt_cant = (await celdas[idx_cant].inner_text()).strip()
                            
                            # Si hay descripción y cantidad, es un producto válido
                            if len(txt_desc) > 2 and any(c.isdigit() for c in txt_cant):
                                item = datos_base.copy()
                                item['descripcion_producto'] = txt_desc
                                item['unidad'] = (await celdas[idx_und].inner_text()).strip()
                                item['cantidad'] = clean_float(txt_cant)
                                item['valor_unitario'] = clean_float(await celdas[idx_vunit].inner_text())
                                item['valor_total'] = clean_float(await celdas[idx_vtotal].inner_text())
                                
                                lista_items.append(item)
                        except Exception as e:
                            print(f"Error parseando fila: {e}")
                            continue

            await browser.close()
            
            # Fallback: Si no se extrajeron filas pero hay total (caso raro), crear ítem genérico
            if not lista_items and gran_total > 0:
                datos_base['descripcion_producto'] = "Detalle general del proceso"
                datos_base['cantidad'] = 1
                datos_base['valor_unitario'] = gran_total
                datos_base['valor_total'] = gran_total
                lista_items.append(datos_base)
                
            return lista_items

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return []