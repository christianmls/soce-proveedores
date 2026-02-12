from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from typing import Optional, Dict
import re

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scrape complete data from compraspublicas.gob.ec
    Extrae: datos del proveedor, productos, valores y archivos
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
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            except PlaywrightTimeout:
                print(f"Timeout loading page for RUC {ruc}")
                await browser.close()
                return None
            
            # Esperar que cargue el contenido
            await page.wait_for_timeout(3000)
            
            # Obtener todo el texto de la página
            texto_completo = await page.inner_text('body')
            
            # Verificar si no hay datos
            if any(palabra in texto_completo.lower() for palabra in ['no se encontr', 'sin datos', 'no existe', 'no registra']):
                await browser.close()
                return None
            
            datos = {}
            
            # ===== EXTRAER DATOS DEL PROVEEDOR =====
            print(f"Extrayendo datos para RUC: {ruc}")
            
            # RUC
            ruc_match = re.search(r'RUC[:\s]+(\d+)', texto_completo, re.IGNORECASE)
            if ruc_match:
                datos['ruc'] = ruc_match.group(1).strip()
            else:
                datos['ruc'] = ruc
            
            # Razón Social
            razon_patterns = [
                r'Razón Social[:\s]+([^\n]+)',
                r'Nombre[:\s]+([^\n]+)',
            ]
            for pattern in razon_patterns:
                razon_match = re.search(pattern, texto_completo, re.IGNORECASE)
                if razon_match:
                    datos['razon_social'] = razon_match.group(1).strip()
                    break
            
            # Correo electrónico
            correo_match = re.search(r'Correo electrónico[:\s]+([^\s\n]+@[^\s\n]+)', texto_completo, re.IGNORECASE)
            if correo_match:
                datos['correo_electronico'] = correo_match.group(1).strip()
            
            # Teléfono
            telefono_match = re.search(r'Teléfono[:\s]+([\d\s\-\(\)]+)', texto_completo, re.IGNORECASE)
            if telefono_match:
                datos['telefono'] = telefono_match.group(1).strip()
            
            # País
            pais_match = re.search(r'País[:\s]+([^\n]+)', texto_completo, re.IGNORECASE)
            if pais_match:
                datos['pais'] = pais_match.group(1).strip()
            
            # Provincia
            provincia_match = re.search(r'Provincia[:\s]+([^\n]+)', texto_completo, re.IGNORECASE)
            if provincia_match:
                datos['provincia'] = provincia_match.group(1).strip()
            
            # Cantón
            canton_match = re.search(r'Cantón[:\s]+([^\n]+)', texto_completo, re.IGNORECASE)
            if canton_match:
                datos['canton'] = canton_match.group(1).strip()
            
            # Dirección
            direccion_match = re.search(r'Dirección[:\s]+([^\n]+)', texto_completo, re.IGNORECASE)
            if direccion_match:
                datos['direccion'] = direccion_match.group(1).strip()
            
            # ===== EXTRAER DATOS DE PRODUCTOS =====
            # Buscar la tabla de productos
            tablas = await page.query_selector_all('table')
            
            producto_encontrado = False
            for tabla in tablas:
                try:
                    # Obtener todas las filas
                    filas = await tabla.query_selector_all('tr')
                    
                    if len(filas) < 2:
                        continue
                    
                    # Revisar el header para confirmar que es la tabla correcta
                    header_row = filas[0]
                    header_text = await header_row.inner_text()
                    
                    # Debe contener columnas de producto
                    if not ('descripci' in header_text.lower() and ('cantidad' in header_text.lower() or 'valor' in header_text.lower())):
                        continue
                    
                    print(f"Tabla de productos encontrada, procesando {len(filas)} filas...")
                    
                    # Procesar filas de datos (saltar header y fila de total)
                    for idx, fila in enumerate(filas[1:]):
                        fila_texto = await fila.inner_text()
                        
                        # Saltar fila si es el total
                        if 'total' in fila_texto.lower() and 'descripci' not in fila_texto.lower():
                            # Extraer el total de esta fila
                            total_match = re.search(r'([\d.,]+)\s*USD', fila_texto, re.IGNORECASE)
                            if total_match:
                                valor_str = total_match.group(1).replace('.', '').replace(',', '.')
                                try:
                                    datos['valor_total'] = float(valor_str)
                                    print(f"Total encontrado en tabla: {datos['valor_total']}")
                                except:
                                    pass
                            continue
                        
                        celdas = await fila.query_selector_all('td')
                        
                        # Debe tener al menos 5 columnas
                        if len(celdas) >= 5:
                            try:
                                # Descripción (columna 0)
                                desc_texto = (await celdas[0].inner_text()).strip()
                                
                                # Verificar que no sea una fila vacía o de encabezado
                                if desc_texto and len(desc_texto) > 10 and not desc_texto.lower().startswith('descripci'):
                                    datos['descripcion_producto'] = desc_texto
                                    
                                    # Unidad (columna 1)
                                    datos['unidad'] = (await celdas[1].inner_text()).strip()
                                    
                                    # Cantidad (columna 2)
                                    cantidad_texto = (await celdas[2].inner_text()).strip()
                                    try:
                                        datos['cantidad'] = float(cantidad_texto.replace(',', '.'))
                                    except:
                                        datos['cantidad'] = 0.0
                                    
                                    # Valor Unitario (columna 3)
                                    valor_unit_texto = (await celdas[3].inner_text()).strip()
                                    # Limpiar: remover USD, puntos de miles, convertir coma decimal a punto
                                    valor_unit_limpio = valor_unit_texto.replace('USD', '').replace('.', '').replace(',', '.').strip()
                                    try:
                                        datos['valor_unitario'] = float(valor_unit_limpio)
                                    except:
                                        datos['valor_unitario'] = 0.0
                                    
                                    # Valor Total por línea (columna 4)
                                    valor_total_linea = (await celdas[4].inner_text()).strip()
                                    valor_total_limpio = valor_total_linea.replace('USD', '').replace('.', '').replace(',', '.').strip()
                                    try:
                                        valor_total_linea_float = float(valor_total_limpio)
                                        # Si no hemos encontrado el total general, usar este
                                        if 'valor_total' not in datos:
                                            datos['valor_total'] = valor_total_linea_float
                                    except:
                                        pass
                                    
                                    producto_encontrado = True
                                    print(f"Producto extraído: {datos['descripcion_producto'][:50]}...")
                                    print(f"  - Unidad: {datos['unidad']}")
                                    print(f"  - Cantidad: {datos['cantidad']}")
                                    print(f"  - Valor Unitario: {datos['valor_unitario']}")
                                    print(f"  - Valor Total: {datos.get('valor_total', 0)}")
                                    break  # Tomamos solo el primer producto
                                    
                            except Exception as e:
                                print(f"Error extrayendo fila de producto: {e}")
                                continue
                    
                    if producto_encontrado:
                        break
                        
                except Exception as e:
                    print(f"Error procesando tabla: {e}")
                    continue
            
            # Si no encontramos el valor total en la tabla de productos, buscarlo al final
            if 'valor_total' not in datos:
                # Buscar en toda la página el TOTAL final
                total_patterns = [
                    r'TOTAL[:\s]+(?:USD\.?)?[\s]*([\d.,]+)\s*USD',
                    r'TOTAL[:\s]+([\d.,]+)',
                    r'Valor Total[:\s]+(?:USD\.?)?[\s]*([\d.,]+)',
                ]
                for pattern in total_patterns:
                    total_match = re.search(pattern, texto_completo, re.IGNORECASE)
                    if total_match:
                        valor_str = total_match.group(1).replace('.', '').replace(',', '.')
                        try:
                            datos['valor_total'] = float(valor_str)
                            print(f"Total encontrado con regex: {datos['valor_total']}")
                            break
                        except:
                            pass
            
            # ===== DETECTAR ARCHIVOS =====
            # Buscar texto que indique archivos adjuntos
            tiene_archivos = bool(re.search(r'archivo|descarg|adjunt|proforma|experiencia', texto_completo, re.IGNORECASE))
            datos['tiene_archivos'] = tiene_archivos
            
            await browser.close()
            
            # Debug: imprimir datos extraídos completos
            print(f"Datos completos extraídos para {ruc}: {datos}")
            
            # Solo retornar si encontramos datos mínimos
            if datos.get('razon_social') or datos.get('descripcion_producto') or datos.get('valor_total'):
                return datos
            
            print(f"No se encontraron datos suficientes para {ruc}")
            return None
            
    except Exception as e:
        print(f"Error scraping RUC {ruc}: {str(e)}")
        import traceback
        traceback.print_exc()
        if browser:
            try:
                await browser.close()
            except:
                pass
        return None