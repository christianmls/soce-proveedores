from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> List[Dict]:
    """
    Retorna una LISTA de diccionarios.
    Cada ítem de la lista representa una fila de producto encontrada en la tabla.
    """
    # Limpieza del ID
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
            
            await page.wait_for_timeout(2500)
            texto_completo = await page.inner_text('body')
            
            if any(p in texto_completo.lower() for p in ['no se encontr', 'sin datos', 'no existe']):
                await browser.close()
                return []
            
            # --- DATOS COMUNES DEL PROVEEDOR ---
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
                clean = re.sub(r'[^\d\.]', '', txt.replace(',', '')) 
                try:
                    return float(clean)
                except:
                    return 0.0

            # --- DETECCIÓN DE ARCHIVOS (Común para todos los ítems) ---
            botones_descarga = await page.query_selector_all("input[type='image'], img[src*='descargar'], img[src*='download'], a[href*='descargar']")
            anexos_section = await page.query_selector("text='Documentos Anexos'")
            tiene_archivos = (len(botones_descarga) > 0) or (anexos_section is not None)
            datos_base['tiene_archivos'] = tiene_archivos

            # --- EXTRACCIÓN FILA POR FILA ---
            filas = await page.query_selector_all('tr')
            
            # Variable para guardar el Gran Total si aparece al final
            gran_total = 0.0

            for fila in filas:
                texto_fila = await fila.inner_text()
                
                # 1. Si es la fila de TOTAL GENERAL
                if "TOTAL:" in texto_fila:
                    celdas = await fila.query_selector_all('td')
                    for celda in celdas:
                        txt = await celda.inner_text()
                        if any(c.isdigit() for c in txt) and "TOTAL" not in txt:
                            gran_total = clean_float(txt)
                    continue 

                # 2. Si es una fila de PRODUCTO
                # Filtros: No debe ser header ("descripción") y debe tener columnas suficientes
                if "descripci" in texto_fila.lower() or "razón social" in texto_fila.lower():
                    continue

                celdas = await fila.query_selector_all('td')
                
                if len(celdas) >= 5:
                    try:
                        # Índices (Layout 7 columnas estándar)
                        idx_desc = 2 if len(celdas) >= 7 else 1
                        idx_und = 3 if len(celdas) >= 7 else 2
                        idx_cant = 4 if len(celdas) >= 7 else 3
                        idx_vunit = 5 if len(celdas) >= 7 else 4
                        idx_vtotal = 6 if len(celdas) >= 7 else 5 # Total de la línea

                        txt_desc = (await celdas[idx_desc].inner_text()).strip()
                        txt_cant = (await celdas[idx_cant].inner_text()).strip()
                        txt_vunit = (await celdas[idx_vunit].inner_text()).strip()
                        
                        # Capturar total de línea si existe columna
                        txt_vtotal_linea = "0"
                        if len(celdas) > idx_vtotal:
                            txt_vtotal_linea = (await celdas[idx_vtotal].inner_text()).strip()

                        # Validación: ¿Parece un producto?
                        es_numero = re.search(r'\d', txt_cant)
                        
                        if len(txt_desc) > 2 and es_numero:
                            # CREAMOS UN DICCIONARIO NUEVO PARA ESTE ÍTEM
                            item = datos_base.copy() # Copia los datos del proveedor
                            
                            item['descripcion_producto'] = txt_desc
                            item['unidad'] = (await celdas[idx_und].inner_text()).strip()
                            item['cantidad'] = clean_float(txt_cant)
                            item['valor_unitario'] = clean_float(txt_vunit)
                            item['valor_total'] = clean_float(txt_vtotal_linea) # Total de ESTA línea
                            
                            lista_items.append(item)
                    except:
                        continue

            await browser.close()
            
            # Ajuste final: Si no encontramos ítems pero sí datos de proveedor, 
            # devolvemos al menos un ítem genérico para que conste el proveedor.
            if not lista_items and datos_base.get('razon_social'):
                 datos_base['descripcion_producto'] = "Sin detalle de productos"
                 datos_base['valor_total'] = gran_total
                 lista_items.append(datos_base)

            return lista_items

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return []