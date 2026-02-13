from playwright.async_api import async_playwright
import re
from typing import Dict, Optional
import asyncio

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    base_url = "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/"
    
    def clean_val(txt: str) -> float:
        if not txt: 
            return 0.0
        clean = txt.replace('USD', '').replace('Unidad', '').strip()
        clean = re.sub(r'[^\d\.]', '', clean)
        try: 
            return float(clean) if clean else 0.0
        except: 
            return 0.0

    browser = None
    context = None
    page = None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(4000)
            
            total_general = 0.0
            items = []
            anexos = []
            datos_proveedor = {}
            
            # ===== EXTRAER DATOS DEL PROVEEDOR =====
            try:
                # Buscar la sección "Datos del Proveedor"
                proveedor_section = await page.query_selector("text=RUC:")
                if proveedor_section:
                    # Obtener el contenedor padre
                    container = await proveedor_section.evaluate_handle("el => el.closest('table, div')")
                    proveedor_text = await container.inner_text() if container else ""
                    
                    # Extraer datos con regex
                    datos_proveedor["ruc"] = ruc
                    
                    razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', proveedor_text, re.IGNORECASE)
                    if razon_match:
                        datos_proveedor["razon_social"] = razon_match.group(1).strip()
                    
                    correo_match = re.search(r'Correo electrónico[:\s]+([^\s\n]+@[^\s\n]+)', proveedor_text, re.IGNORECASE)
                    if correo_match:
                        datos_proveedor["correo"] = correo_match.group(1).strip()
                    
                    telefono_match = re.search(r'Teléfono[:\s]+([\d\s\-]+)', proveedor_text, re.IGNORECASE)
                    if telefono_match:
                        datos_proveedor["telefono"] = telefono_match.group(1).strip()
                    
                    pais_match = re.search(r'País[:\s]+([^\n]+)', proveedor_text, re.IGNORECASE)
                    if pais_match:
                        datos_proveedor["pais"] = pais_match.group(1).strip()
                    
                    provincia_match = re.search(r'Provincia[:\s]+([^\n]+)', proveedor_text, re.IGNORECASE)
                    if provincia_match:
                        datos_proveedor["provincia"] = provincia_match.group(1).strip()
                    
                    canton_match = re.search(r'Cantón[:\s]+([^\n]+)', proveedor_text, re.IGNORECASE)
                    if canton_match:
                        datos_proveedor["canton"] = canton_match.group(1).strip()
                    
                    direccion_match = re.search(r'Dirección[:\s]+([^\n]+)', proveedor_text, re.IGNORECASE)
                    if direccion_match:
                        datos_proveedor["direccion"] = direccion_match.group(1).strip()
                    
                    print(f"✓ Datos del proveedor extraídos: {datos_proveedor.get('razon_social', 'N/A')}")
            except Exception as e:
                print(f"Error extrayendo datos del proveedor: {e}")

            # ===== EXTRAER ITEMS Y TOTAL =====
            rows = await page.query_selector_all("table tr")
            
            for row in rows:
                cells = await row.query_selector_all("td")
                row_text = await row.inner_text()
                
                # FILA DE TOTAL
                if "TOTAL:" in row_text.upper() and "**" in row_text:
                    total_match = re.search(r'\*\*(\d+\.?\d*)\*\*', row_text)
                    if total_match:
                        total_general = float(total_match.group(1))
                        print(f"✓ Total: {total_general}")
                    else:
                        if len(cells) >= 2:
                            for i in range(len(cells)-1, max(len(cells)-4, -1), -1):
                                cell_text = await cells[i].inner_text()
                                if cell_text and re.search(r'\d', cell_text) and 'USD' not in cell_text.upper():
                                    val = clean_val(cell_text)
                                    if val > 0:
                                        total_general = val
                                        break
                    continue
                
                # FILAS DE PRODUCTOS (9 columnas)
                if len(cells) == 9:
                    try:
                        numero = (await cells[0].inner_text()).strip()
                        
                        if numero and numero.isdigit():
                            cpc = (await cells[1].inner_text()).strip()
                            nombre_producto = (await cells[2].inner_text()).strip()
                            descripcion = (await cells[3].inner_text()).strip()
                            unidad = (await cells[4].inner_text()).strip()
                            cantidad = clean_val(await cells[5].inner_text())
                            v_unitario = clean_val(await cells[6].inner_text())
                            v_total = clean_val(await cells[7].inner_text())
                            
                            items.append({
                                "numero": numero,
                                "cpc": cpc,
                                "desc": f"[{cpc}] {nombre_producto} - {descripcion}",
                                "unid": unidad,
                                "cant": cantidad,
                                "v_unit": v_unitario,
                                "v_tot": v_total
                            })
                            
                            print(f"✓ Item {numero}: ${v_total}")
                    except:
                        continue

            # ===== EXTRAER ANEXOS CON LINKS DEL HREF =====
            try:
                all_tables = await page.query_selector_all("table")
                
                for table in all_tables:
                    table_text = await table.inner_text()
                    
                    if "ARCHIVO" in table_text.upper() or "ANEXO" in table_text.upper() or "Proforma" in table_text:
                        print(f"✓ Procesando tabla de anexos...")
                        
                        table_rows = await table.query_selector_all("tr")
                        
                        for trow in table_rows:
                            tcells = await trow.query_selector_all("td")
                            
                            if len(tcells) >= 2:
                                # Primera celda = nombre
                                nombre_archivo = (await tcells[0].inner_text()).strip()
                                
                                # Segunda celda = buscar el <a href>
                                download_url = None
                                link_element = await tcells[1].query_selector("a")
                                
                                if link_element:
                                    # Obtener el href
                                    href = await link_element.get_attribute("href")
                                    
                                    if href:
                                        # Convertir a URL absoluta
                                        if href.startswith('../'):
                                            # ../GE/... -> https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/GE/...
                                            relative_url = href.replace('../', '')
                                            download_url = base_url + relative_url
                                        elif href.startswith('/'):
                                            download_url = "https://www.compraspublicas.gob.ec" + href
                                        else:
                                            download_url = base_url + href
                                        
                                        print(f"✓ Link extraído: {download_url}")
                                
                                # Validar nombre
                                excluir = [
                                    "descripción", "archivo", "descargar", "adjuntar",
                                    "adicional", "observaciones", "publicación", "opcional", ""
                                ]
                                
                                es_valido = (
                                    nombre_archivo and
                                    len(nombre_archivo) > 2 and
                                    not any(exc in nombre_archivo.lower() for exc in excluir) and
                                    not nombre_archivo.startswith("**")
                                )
                                
                                if es_valido and download_url and not any(a["nombre"] == nombre_archivo for a in anexos):
                                    anexos.append({
                                        "nombre": nombre_archivo,
                                        "url": download_url
                                    })
                                    print(f"✓ Anexo guardado: {nombre_archivo}")
                
            except Exception as e:
                print(f"Error extrayendo anexos: {e}")
                import traceback
                traceback.print_exc()

            # Cerrar navegador
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
            
            resultado = {
                "total": total_general,
                "items": items,
                "anexos": anexos,
                "proveedor": datos_proveedor  # <-- NUEVO
            }
            
            print(f"✅ RUC {ruc}: {len(items)} items, Total=${total_general}, {len(anexos)} anexos")
            return resultado
            
    except Exception as e:
        print(f"❌ Error scraping RUC {ruc}: {str(e)}")
        try:
            if page: await page.close()
            if context: await context.close()
            if browser: await browser.close()
        except:
            pass
        return None