from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import Optional, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scraper Multi-Fila:
    1. Recorre TODAS las filas de productos para concatenar descripciones.
    2. Extrae el TOTAL oficial del pie de página.
    3. Detecta archivos adjuntos.
    """
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={proceso_id}&ruc={ruc}"
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            
            # Cargar página
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except PlaywrightTimeout:
                print(f"Timeout cargando RUC {ruc}")
                await browser.close()
                return None
            
            await page.wait_for_timeout(2000)
            texto_completo = await page.inner_text('body')
            
            # Validar existencia
            if any(p in texto_completo.lower() for p in ['no se encontr', 'sin datos', 'no existe']):
                await browser.close()
                return None
            
            datos = {}
            datos['ruc'] = ruc 

            # ===== 1. DATOS DEL PROVEEDOR (Regex) =====
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
                        datos[key] = match.group(1).strip()
                        break
            
            # Helper numérico
            def clean_float(txt):
                if not txt: return 0.0
                # Eliminar $ y USD, y comas de miles
                t = txt.replace('USD', '').replace('$', '').strip()
                t = t.replace(',', '') 
                try:
                    return float(t)
                except:
                    return 0.0

            # ===== 2. TABLA DE PRODUCTOS (MULTI-FILA) =====
            descripciones = []
            cantidades = []
            
            tablas = await page.query_selector_all('table')
            
            for tabla in tablas:
                header_text = await tabla.inner_text()
                # Verificar que sea la tabla de productos
                if not ('descripci' in header_text.lower() and 'valor' in header_text.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                
                for fila in filas:
                    texto_fila = await fila.inner_text()
                    celdas = await fila.query_selector_all('td')

                    # A) BUSCAR TOTAL (Prioridad)
                    if "TOTAL:" in texto_fila:
                        for celda in celdas:
                            txt = await celda.inner_text()
                            # Si es número y no es la etiqueta "TOTAL"
                            if any(c.isdigit() for c in txt) and "TOTAL" not in txt:
                                val = clean_float(txt)
                                if val > 0:
                                    datos['valor_total'] = val
                        continue # No intentamos procesar esta fila como producto

                    # B) BUSCAR PRODUCTO
                    # Filtro: debe tener columnas suficientes y no ser header
                    if len(celdas) >= 6 and "descripci" not in texto_fila.lower():
                        try:
                            # Índices dinámicos (ajuste por columna 'No.')
                            idx_desc = 2 if len(celdas) >= 7 else 1
                            idx_cant = 4 if len(celdas) >= 7 else 3
                            idx_vunit = 5 if len(celdas) >= 7 else 4

                            desc_text = (await celdas[idx_desc].inner_text()).strip()
                            
                            # Validar que sea un producto real
                            if len(desc_text) > 2:
                                descripciones.append(desc_text)
                                cantidades.append(clean_float(await celdas[idx_cant].inner_text()))
                                
                                # Guardamos el primer valor unitario como referencia
                                if 'valor_unitario' not in datos:
                                    datos['valor_unitario'] = clean_float(await celdas[idx_vunit].inner_text())
                        except:
                            continue
                
                # Si encontramos productos en esta tabla, asumimos que es la correcta y salimos
                if descripciones:
                    break

            # ===== 3. CONSOLIDACIÓN =====
            if descripciones:
                # Si hay más de 1 producto, creamos un resumen
                if len(descripciones) > 1:
                    # Ejemplo: "Hosting + Dominio (2 ítems)"
                    resumen = " + ".join(descripciones)
                    # Si es muy largo, lo cortamos
                    if len(resumen) > 150:
                        resumen = f"{descripciones[0]} y {len(descripciones)-1} más..."
                    datos['descripcion_producto'] = resumen
                    datos['unidad'] = "Varios"
                else:
                    datos['descripcion_producto'] = descripciones[0]
                    datos['unidad'] = "Unidad" # O extraer de la tabla si es crítico
                
                datos['cantidad'] = sum(cantidades)
            
            # Respaldo para el total si falló la lectura de tabla
            if 'valor_total' not in datos:
                match_total = re.search(r'TOTAL[:\s]+([\d\.]+)', texto_completo)
                if match_total:
                    datos['valor_total'] = float(match_total.group(1))

            # ===== 4. ARCHIVOS / ANEXOS =====
            # Buscamos botones de descarga (imágenes o inputs)
            botones_descarga = await page.query_selector_all("input[type='image'], img[src*='descargar'], img[src*='download']")
            
            # O enlaces explícitos
            enlaces_descarga = await page.query_selector_all("a[href*='descargar']")
            
            # O sección de texto
            anexos_section = await page.query_selector("text='Documentos Anexos'")
            
            datos['tiene_archivos'] = len(botones_descarga) > 0 or len(enlaces_descarga) > 0 or (anexos_section is not None)

            await browser.close()
            
            if datos.get('razon_social') or datos.get('valor_total'):
                return datos
            return None

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return None