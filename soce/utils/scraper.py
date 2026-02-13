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
            datos_proveedor = {
                "ruc": ruc,
                "razon_social": "",
                "correo": "",
                "telefono": "",
                "pais": "",
                "provincia": "",
                "canton": "",
                "direccion": ""
            }
            
            # ===== EXTRAER DATOS DEL PROVEEDOR =====
            try:
                content = await page.content()
                
                # Buscar RUC
                ruc_match = re.search(r'<strong>RUC:</strong>\s*</td>\s*<td[^>]*>\s*([^\s<]+)', content)
                if ruc_match:
                    datos_proveedor["ruc"] = ruc_match.group(1).strip()
                
                # Buscar Razón Social
                razon_match = re.search(r'<strong>Razón Social:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if razon_match:
                    datos_proveedor["razon_social"] = razon_match.group(1).strip()
                
                # Buscar Correo
                correo_match = re.search(r'<strong>Correo electrónico:</strong>\s*</td>\s*<td[^>]*>\s*([^<\s]+@[^<\s]+)', content)
                if correo_match:
                    datos_proveedor["correo"] = correo_match.group(1).strip()
                
                # Buscar Teléfono
                telefono_match = re.search(r'<strong>Teléfono:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if telefono_match:
                    datos_proveedor["telefono"] = telefono_match.group(1).strip()
                
                # Buscar País
                pais_match = re.search(r'<strong>País:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if pais_match:
                    datos_proveedor["pais"] = pais_match.group(1).strip()
                
                # Buscar Provincia
                provincia_match = re.search(r'<strong>Provincia:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if provincia_match:
                    datos_proveedor["provincia"] = provincia_match.group(1).strip()
                
                # Buscar Cantón
                canton_match = re.search(r'<strong>Cantón:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if canton_match:
                    datos_proveedor["canton"] = canton_match.group(1).strip()
                
                # Buscar Dirección
                direccion_match = re.search(r'<strong>Dirección:</strong>\s*</td>\s*<td[^>]*>\s*([^<]+)', content)
                if direccion_match:
                    datos_proveedor["direccion"] = direccion_match.group(1).strip()
                
                print(f"✓ Proveedor: {datos_proveedor['razon_social']} ({datos_proveedor['ruc']})")
                
            except Exception as e:
                print(f"Error extrayendo datos del proveedor: {e}")

            # ===== EXTRAER ITEMS Y TOTAL =====
            rows = await page.query_selector_all("table tr")
            
            for row in rows:
                cells = await row.query_selector_all("td")
                row_text = await row.inner_text()
                
                if "TOTAL:" in row_text.upper() and "**" in row_text:
                    total_match = re.search(r'\*\*(\d+\.?\d*)\*\*', row_text)
                    if total_match:
                        total_general = float(total_match.group(1))
                        print(f"✓ Total: {total_general}")
                    continue
                
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

            # ===== EXTRAER ANEXOS CON HREF CORRECTO =====
            try:
                # Obtener el HTML completo
                html_content = await page.content()
                
                # Buscar todos los enlaces de descarga con regex
                # Patrón: <a href="../GE/ExeGENBajarArchivoGeneral.cpe?Archivo=...&idPath=...">
                patron_links = re.finditer(
                    r'<a\s+href="(\.\./GE/ExeGENBajarArchivoGeneral\.cpe\?[^"]+)"[^>]*>',
                    html_content
                )
                
                for match in patron_links:
                    href_relativo = match.group(1)
                    
                    # Convertir a URL absoluta
                    # ../GE/... -> https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/GE/...
                    url_absoluta = base_url + href_relativo.replace('../', '')
                    
                    # Buscar el nombre del archivo en la fila anterior
                    # El patrón usual es <td>NombreArchivo</td> seguido del <td> con el link
                    pos_link = match.start()
                    fragmento_antes = html_content[max(0, pos_link-500):pos_link]
                    
                    # Buscar el último <td> antes del link
                    td_match = re.search(r'<td[^>]*>\s*([^<]+?)\s*</td>\s*$', fragmento_antes)
                    if td_match:
                        nombre_archivo = td_match.group(1).strip()
                        
                        # Validar que no sea un header
                        if nombre_archivo and len(nombre_archivo) > 2 and \
                           nombre_archivo not in ["Descripción del Archivo", "Descargar Archivo", ""]:
                            
                            anexos.append({
                                "nombre": nombre_archivo,
                                "url": url_absoluta
                            })
                            print(f"✓ Anexo: {nombre_archivo} -> {url_absoluta[:80]}...")
                
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
                "proveedor": datos_proveedor
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