from playwright.async_api import async_playwright
import re
from typing import Dict, Optional
import asyncio


async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    def clean_val(txt: str) -> float:
        """Limpia valores numéricos manteniendo el punto decimal"""
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
            
            content = await page.content()
            
            # ===== EXTRAER ITEMS Y TOTAL =====
            rows = await page.query_selector_all("table tr")
            
            for row in rows:
                cells = await row.query_selector_all("td")
                row_text = await row.inner_text()
                
                # FILA DE TOTAL
                if "TOTAL:" in row_text.upper():
                    if len(cells) >= 2:
                        try:
                            for i in range(len(cells)-1, max(len(cells)-4, -1), -1):
                                cell_text = await cells[i].inner_text()
                                if cell_text and re.search(r'\d', cell_text) and 'USD' not in cell_text.upper():
                                    val = clean_val(cell_text)
                                    if val > 0:
                                        total_general = val
                                        print(f"✓ Total general: {total_general}")
                                        break
                        except Exception as e:
                            print(f"Error extrayendo total: {e}")
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
                        print(f"Error procesando fila: {e}")
                        continue

            # ===== EXTRAER ANEXOS =====
            try:
                anexo_tables = await page.query_selector_all("table")
                
                for table in anexo_tables:
                    table_text = await table.inner_text()
                    
                    if "ARCHIVO PARA ADJUNTAR" in table_text.upper() or "DESCRIPCIÓN DEL ARCHIVO" in table_text.upper():
                        print("✓ Tabla de anexos encontrada")
                        
                        anexo_rows = await table.query_selector_all("tr")
                        
                        for arow in anexo_rows:
                            acells = await arow.query_selector_all("td")
                            
                            if len(acells) >= 1:
                                nombre_archivo = (await acells[0].inner_text()).strip()
                                
                                palabras_excluir = [
                                    "descripción", "archivo para adjuntar", "descargar archivo",
                                    "descripción del archivo", ""
                                ]
                                
                                es_valido = (
                                    nombre_archivo and 
                                    len(nombre_archivo) > 2 and
                                    not any(excl in nombre_archivo.lower() for excl in palabras_excluir)
                                )
                                
                                if es_valido:
                                    if not any(a["nombre"] == nombre_archivo for a in anexos):
                                        anexos.append({
                                            "nombre": nombre_archivo,
                                            "url": url
                                        })
                                        print(f"✓ Anexo: {nombre_archivo}")
                
                # Fallback: búsqueda con regex
                if len(anexos) == 0:
                    anexo_patterns = [
                        r'PROFORMA',
                        r'EXPERIENCIA[^\n]*VIDA',
                        r'HOJA DE VIDA',
                        r'CERTIFICADO',
                        r'RUC',
                    ]
                    
                    for pattern in anexo_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            nombre = match.group(0).strip()
                            if nombre and not any(a["nombre"] == nombre for a in anexos):
                                anexos.append({
                                    "nombre": nombre,
                                    "url": url
                                })
                                print(f"✓ Anexo (regex): {nombre}")
                
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