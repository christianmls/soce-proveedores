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
                texto_tabla = await tabla.inner_text()
                
                # Verificar si es la tabla de productos
                if 'descripci' in texto_tabla.lower() and ('producto' in texto_tabla.lower() or 'valor' in texto_tabla.lower()):
                    filas = await tabla.query_selector_all('tr')
                    
                    # Buscar la fila con datos (generalmente la segunda fila)
                    for idx, fila in enumerate(filas):
                        if idx == 0:  # Saltar header
                            continue
                            
                        celdas = await fila.query_selector_all('td')
                        
                        # Debe tener al menos 5 columnas: descripción, unidad, cantidad, valor unitario, valor total
                        if len(celdas) >= 5:
                            try:
                                # Descripción del producto
                                desc_texto = await celdas[0].inner_text()
                                if desc_texto and len(desc_texto.strip()) > 10 and 'total' not in desc_texto.lower():
                                    datos['descripcion_producto'] = desc_texto.strip()
                                    
                                    # Unidad
                                    datos['unidad'] = (await celdas[1].inner_text()).strip()
                                    
                                    # Cantidad
                                    cantidad_texto = (await celdas[2].inner_text()).strip()
                                    try:
                                        datos['cantidad'] = float(cantidad_texto.replace(',', '.'))
                                    except:
                                        datos['cantidad'] = 0.0
                                    
                                    # Valor Unitario
                                    valor_unit_texto = (await celdas[3].inner_text()).replace('USD', '').replace('.', '').replace(',', '.').strip()
                                    try:
                                        datos['valor_unitario'] = float(valor_unit_texto)
                                    except:
                                        datos['valor_unitario'] = 0.0
                                    
                                    # Valor Total
                                    valor_total_texto = (await celdas[4].inner_text()).replace('USD', '').replace('.', '').replace(',', '.').strip()
                                    try:
                                        datos['valor_total'] = float(valor_total_texto)
                                    except:
                                        datos['valor_total'] = 0.0
                                    
                                    producto_encontrado = True
                                    break
                            except Exception as e:
                                print(f"Error extrayendo fila de producto: {e}")
                                continue
                    
                    if producto_encontrado:
                        break
            
            # Si no encontramos producto en tabla, intentar con regex
            if not producto_encontrado:
                # Buscar valor total con regex
                total_patterns = [
                    r'TOTAL[:\s]+(?:USD\.?)?[\s]*([\d.,]+)',
                    r'Valor Total[:\s]+(?:USD\.?)?[\s]*([\d.,]+)',
                ]
                for pattern in total_patterns:
                    total_match = re.search(pattern, texto_completo, re.IGNORECASE)
                    if total_match:
                        valor_str = total_match.group(1).replace('.', '').replace(',', '.')
                        try:
                            datos['valor_total'] = float(valor_str)
                        except:
                            pass
                        break
            
            # ===== DETECTAR ARCHIVOS =====
            # Buscar texto que indique archivos adjuntos
            tiene_archivos = bool(re.search(r'archivo|descarg|adjunt|proforma|experiencia', texto_completo, re.IGNORECASE))
            datos['tiene_archivos'] = tiene_archivos
            
            await browser.close()
            
            # Debug: imprimir datos extraídos
            print(f"Datos extraídos para {ruc}: {datos}")
            
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