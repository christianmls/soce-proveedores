from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import Optional, Dict

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scraper optimizado para compraspublicas.gob.ec
    Corregido para:
    1. Detectar TOTAL en el footer de la tabla.
    2. Detectar archivos en sección 'Documentos Anexos' (iconos de descarga).
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
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=25000)
            except PlaywrightTimeout:
                print(f"Timeout cargando RUC {ruc}")
                await browser.close()
                return None
            
            await page.wait_for_timeout(2000)
            texto_completo = await page.inner_text('body')
            
            if any(p in texto_completo.lower() for p in ['no se encontr', 'sin datos', 'no existe']):
                await browser.close()
                return None
            
            datos = {}
            datos['ruc'] = ruc 

            # ===== 1. DATOS DEL PROVEEDOR =====
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
            
            # Helper para limpiar números (Manejo de punto decimal)
            def clean_float(txt):
                if not txt: return 0.0
                # Eliminar USD, espacios y comas (si son separadores de miles)
                t = txt.replace('USD', '').replace('$', '').strip()
                t = t.replace(',', '') 
                try:
                    return float(t)
                except:
                    return 0.0

            # ===== 2. TABLA DE PRODUCTOS Y TOTAL =====
            tablas = await page.query_selector_all('table')
            
            for tabla in tablas:
                header_text = await tabla.inner_text()
                if not ('descripci' in header_text.lower() and 'valor' in header_text.lower()):
                    continue
                
                filas = await tabla.query_selector_all('tr')
                
                # A) BUSCAR EL TOTAL (Prioridad alta)
                # Buscamos específicamente la fila que contiene "TOTAL:"
                # En tu captura, el total está en la última fila alineado a la derecha
                total_encontrado = False
                for fila in reversed(filas): # Buscamos desde abajo hacia arriba
                    texto_fila = await fila.inner_text()
                    if "TOTAL:" in texto_fila:
                        # Buscamos la celda que tenga el número
                        celdas_total = await fila.query_selector_all('td')
                        for celda in celdas_total:
                            txt = await celda.inner_text()
                            # Si parece un número y no es la palabra "TOTAL:"
                            if any(c.isdigit() for c in txt) and "TOTAL" not in txt:
                                datos['valor_total'] = clean_float(txt)
                                total_encontrado = True
                                break
                    if total_encontrado: break

                # B) EXTRACCIÓN DE PRODUCTOS
                for fila in filas[1:]:
                    texto_fila = await fila.inner_text()
                    # Ignorar fila de total si la encontramos aquí
                    if "TOTAL:" in texto_fila: continue

                    celdas = await fila.query_selector_all('td')
                    
                    # La tabla tiene 7 columnas según tu imagen
                    if len(celdas) >= 6:
                        try:
                            # Ajuste dinámico de índices
                            idx_desc = 2 if len(celdas) >= 7 else 1
                            idx_und = 3 if len(celdas) >= 7 else 2
                            idx_cant = 4 if len(celdas) >= 7 else 3
                            idx_vunit = 5 if len(celdas) >= 7 else 4
                            idx_vtotal = 6 if len(celdas) >= 7 else 5

                            texto_desc = await celdas[idx_desc].inner_text()
                            
                            if len(texto_desc) > 3:
                                datos['descripcion_producto'] = texto_desc.strip()
                                datos['unidad'] = (await celdas[idx_und].inner_text()).strip()
                                datos['cantidad'] = clean_float(await celdas[idx_cant].inner_text())
                                datos['valor_unitario'] = clean_float(await celdas[idx_vunit].inner_text())
                                
                                # Si falló la búsqueda del total abajo, usamos la suma de líneas
                                if 'valor_total' not in datos:
                                    datos['valor_total'] = clean_float(await celdas[idx_vtotal].inner_text())
                                
                                break # Tomamos el primer producto principal
                        except:
                            continue
                
                if 'descripcion_producto' in datos:
                    break

            # ===== 3. ARCHIVOS / ANEXOS (Corregido) =====
            # En tu captura, los archivos tienen un icono azul de descarga.
            # Suelen ser inputs tipo image o imgs dentro de un enlace.
            
            # Estrategia 1: Buscar en la sección "Documentos Anexos"
            # Buscamos cualquier input type='image' o img que parezca un botón de descarga
            
            botones_descarga = await page.query_selector_all("input[type='image'], img[src*='download'], img[src*='descargar'], img[src*='ico_descargar']")
            
            # Filtramos para asegurarnos que están en la zona de contenidos (evitar header/footer del sitio)
            datos['tiene_archivos'] = len(botones_descarga) > 0
            
            # Estrategia 2 (Respaldo): Buscar texto explícito en filas
            if not datos['tiene_archivos']:
                anexos_text = await page.content()
                if "Documentos Anexos" in anexos_text:
                    # Si existe la sección y hay filas con "Descargar Archivo"
                    filas_descarga = await page.query_selector_all("tr:has-text('Descargar Archivo')")
                    if len(filas_descarga) > 0:
                        datos['tiene_archivos'] = True

            await browser.close()
            
            if datos.get('razon_social') or datos.get('valor_total'):
                return datos
            return None

    except Exception as e:
        print(f"Error scraping {ruc}: {e}")
        if browser: await browser.close()
        return None