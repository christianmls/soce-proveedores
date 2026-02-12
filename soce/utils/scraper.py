from playwright.async_api import async_playwright
import re
from typing import Dict, Optional
import asyncio

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
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
            
            # ===== EXTRAER ITEMS Y TOTAL =====
            rows = await page.query_selector_all("table tr")
            
            for row in rows:
                cells = await row.query_selector_all("td")
                row_text = await row.inner_text()
                
                # FILA DE TOTAL - Búsqueda más específica
                if "TOTAL:" in row_text.upper() and "**" in row_text:
                    print(f"✓ Fila TOTAL encontrada: {row_text[:100]}")
                    # Buscar el número en negrita entre **
                    total_match = re.search(r'\*\*(\d+\.?\d*)\*\*', row_text)
                    if total_match:
                        total_general = float(total_match.group(1))
                        print(f"✓ Total extraído: {total_general}")
                    else:
                        # Fallback: buscar en celdas
                        if len(cells) >= 2:
                            for i in range(len(cells)-1, max(len(cells)-4, -1), -1):
                                cell_text = await cells[i].inner_text()
                                if cell_text and re.search(r'\d', cell_text) and 'USD' not in cell_text.upper():
                                    val = clean_val(cell_text)
                                    if val > 0:
                                        total_general = val
                                        print(f"✓ Total (fallback): {total_general}")
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
                    except Exception as e:
                        continue

            # ===== EXTRAER ANEXOS - MEJORADO =====
            try:
                # Buscar todas las tablas con "ARCHIVO"
                all_tables = await page.query_selector_all("table")
                
                for table in all_tables:
                    table_html = await table.inner_html()
                    table_text = await table.inner_text()
                    
                    # Solo procesar tablas de anexos
                    if "ARCHIVO" in table_text.upper() and ("ADJUNTAR" in table_text.upper() or "ADICIONAL" in table_text.upper()):
                        print(f"✓ Procesando tabla de anexos...")
                        
                        # Obtener filas
                        table_rows = await table.query_selector_all("tr")
                        
                        for trow in table_rows:
                            tcells = await trow.query_selector_all("td")
                            
                            # Primera celda = nombre del archivo
                            if len(tcells) >= 1:
                                nombre_archivo = (await tcells[0].inner_text()).strip()
                                
                                # Filtros estrictos
                                excluir = [
                                    "descripción", "archivo", "descargar", "adjuntar",
                                    "adicional", "observaciones", "publicación", "opcional"
                                ]
                                
                                # Validar
                                es_valido = (
                                    nombre_archivo and
                                    len(nombre_archivo) > 2 and
                                    not any(exc in nombre_archivo.lower() for exc in excluir) and
                                    not nombre_archivo.startswith("**")
                                )
                                
                                if es_valido and not any(a["nombre"] == nombre_archivo for a in anexos):
                                    anexos.append({
                                        "nombre": nombre_archivo,
                                        "url": url
                                    })
                                    print(f"✓ Anexo agregado: {nombre_archivo}")
                
            except Exception as e:
                print(f"Error extrayendo anexos: {e}")

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
                "anexos": anexos
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