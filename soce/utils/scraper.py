from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import Optional, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scraper optimizado para compraspublicas.gob.ec
    Maneja formato de tabla de 7 columnas y decimales con punto.
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
                await page.goto(url, wait_until='domcontentloaded', timeout=25000)
            except PlaywrightTimeout:
                print(f"Timeout cargando RUC {ruc}")
                await browser.close()
                return None
            
            await page.wait_for_timeout(2000)
            texto_completo = await page.inner_text('body')
            
            # Validación básica de contenido
            if any(p in texto_completo.lower() for p in ['no se encontr', 'sin datos', 'no existe']):
                await browser.close()
                return None
            
            datos = {}
            
            # ===== 1. DATOS DEL PROVEEDOR =====
            # Extracción por Regex más flexible
            patterns = {
                'razon_social': [r'Razón Social[:\s]+([^\n]+)', r'Nombre[:\s]+([^\n]+)'],
                'correo_electronico': [r'Correo electrónico[:\s]+([^\s\n]+@[^\s\n]+)'],
                'telefono': [r'Teléfono[:\s]+([\d\s\-\(\)]+)'],
                'pais': [r'País[:\s]+([^\n]+)'],
                'provincia': [r'Provincia[:\s]+([^\n]+)'],
                'canton': [r'Cantón[:\s]+([^\n]+)'],
                'direccion': [r'Dirección[:\s]+([^\n]+)']
            }

            datos['ruc'] = ruc # Por defecto el que buscamos
            
            for key, pat_list in patterns.items():
                for pat in pat_list:
                    match = re.search(pat, texto_completo, re.IGNORECASE)
                    if match:
                        datos[key] = match.group(1).strip()
                        break
            
            # ===== 2. TABLA DE PRODUCTOS =====
            tablas = await page.query_selector_all('table')
            
            for tabla in tablas:
                # Buscar tabla que tenga "Descripción" y "Valor" en el header
                header_text = await tabla.inner_text()
                if not ('descripci' in header_text.lower() and 'valor' in header_text.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                
                # Iterar filas (saltando header)
                for fila in filas[1:]:
                    celdas = await fila.query_selector_all('td')
                    texto_fila = await fila.inner_text()

                    # Caso especial: Fila de TOTAL al final de la tabla
                    if 'total' in texto_fila.lower() and len(celdas) < 4:
                        # Extraer el valor total final si aparece aquí
                        val_match = re.search(r'([\d\.]+)', texto_fila)
                        if val_match:
                            try:
                                datos['valor_total'] = float(val_match.group(1))
                            except: pass
                        continue

                    # Estructura esperada (7 columnas):
                    # [0]No. | [1]CPC | [2]Descripción | [3]Unidad | [4]Cant | [5]V.Unit | [6]V.Total
                    if len(celdas) >= 6:
                        try:
                            # Índice 2: Descripción (A veces es columna 1 si no hay CPC, verificamos)
                            # Estrategia: Buscar la celda más ancha o por posición relativa
                            
                            # Ajuste para la tabla mostrada en imagen (7 cols)
                            idx_desc = 2
                            idx_und = 3
                            idx_cant = 4
                            idx_vunit = 5
                            idx_vtotal = 6
                            
                            # Si hay menos celdas, ajustar índices (a veces "No." no está)
                            if len(celdas) == 6:
                                idx_desc = 1; idx_und = 2; idx_cant = 3; idx_vunit = 4; idx_vtotal = 5

                            texto_desc = await celdas[idx_desc].inner_text()
                            
                            # Validar que sea una fila de producto real
                            if len(texto_desc) > 3 and "total" not in texto_desc.lower():
                                datos['descripcion_producto'] = texto_desc.strip()
                                datos['unidad'] = (await celdas[idx_und].inner_text()).strip()
                                
                                # --- PARSEO DE NÚMEROS (CRÍTICO) ---
                                # El sitio usa PUNTO para decimales: "278.00000" -> 278.0
                                def clean_float(txt):
                                    # Quitar USD y espacios
                                    t = txt.replace('USD', '').strip()
                                    # Si hay comas, asumimos que son miles y las quitamos (ej: 1,200.50 -> 1200.50)
                                    # Pero si el sitio usa formato inglés (1200.50), float() lo entiende directo.
                                    t = t.replace(',', '') 
                                    try:
                                        return float(t)
                                    except:
                                        return 0.0

                                datos['cantidad'] = clean_float(await celdas[idx_cant].inner_text())
                                datos['valor_unitario'] = clean_float(await celdas[idx_vunit].inner_text())
                                
                                v_total_linea = clean_float(await celdas[idx_vtotal].inner_text())
                                
                                # Usar este total si no tenemos uno global
                                if 'valor_total' not in datos or datos['valor_total'] == 0:
                                    datos['valor_total'] = v_total_linea
                                
                                # Solo tomamos el primer producto principal encontrado
                                break
                        except Exception as e:
                            # print(f"Error parsing row: {e}")
                            continue
                
                # Si ya encontramos producto, no mirar más tablas
                if 'descripcion_producto' in datos:
                    break

            # ===== 3. ARCHIVOS / ANEXOS =====
            # Buscar enlaces de descarga reales, no solo texto
            # Buscamos iconos de descarga o links que contengan 'descargar'
            links_descarga = await page.query_selector_all("a[href*='descargar'], img[src*='download'], img[src*='descargar']")
            
            # O buscamos en la sección específica "Documentos Anexos"
            seccion_archivos = await page.query_selector("text='Documentos Anexos'")
            
            if links_descarga or seccion_archivos:
                 # Verificación doble: contar filas en la tabla de anexos si existe
                 filas_anexos = await page.query_selector_all("table#tablaAnexos tr") # ID hipotético común
                 if not filas_anexos:
                     # Búsqueda genérica de tabla con "Descargar"
                     filas_anexos = await page.query_selector_all("tr:has-text('Descargar')")
                 
                 datos['tiene_archivos'] = len(links_descarga) > 0 or len(filas_anexos) > 0
            else:
                datos['tiene_archivos'] = False

            await browser.close()
            
            # Validación final
            if datos.get('razon_social') or datos.get('valor_total'):
                return datos
            return None

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return None