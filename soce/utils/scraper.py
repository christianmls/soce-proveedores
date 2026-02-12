from playwright.async_api import async_playwright
import re
from typing import Dict, Optional
import asyncio

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
        # Remover USD, puntos de miles (.) y reemplazar coma decimal por punto
        clean = txt.replace('USD', '').replace('.', '').replace(',', '.').strip()
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
            
            # OBTENER TABLA COMPLETA
            total_general = 0.0
            items = []
            
            # Buscar todas las filas de la tabla
            rows = await page.query_selector_all("table tr")
            
            for row in rows:
                cells = await row.query_selector_all("td")
                row_text = await row.inner_text()
                
                # FILA DE TOTAL
                if "TOTAL:" in row_text.upper():
                    # El total está en la penúltima celda antes de "USD."
                    if len(cells) >= 2:
                        try:
                            total_text = await cells[-2].inner_text()
                            total_general = clean_val(total_text)
                            print(f"✓ Total general encontrado: {total_general}")
                        except Exception as e:
                            print(f"Error extrayendo total: {e}")
                    continue
                
                # FILAS DE PRODUCTOS
                # La tabla tiene 9 columnas: No. | CPC | (vacía) | Desc | Unidad | Cantidad | V.Unit | V.Total | (vacía)
                if len(cells) == 9:
                    try:
                        numero = (await cells[0].inner_text()).strip()
                        
                        # Verificar que es una fila de producto (número válido)
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
                            
                            print(f"✓ Item {numero}: CPC={cpc}, Total={v_total}")
                    except Exception as e:
                        print(f"Error procesando fila: {e}")
                        continue

            # ANEXOS - Mejorado
            anexos = []
            try:
                # Buscar sección de "Documentos Anexos"
                anexo_section = await page.query_selector_all("table")
                
                for table in anexo_section:
                    table_text = await table.inner_text()
                    if "ARCHIVO PARA ADJUNTAR" in table_text.upper() or "DOCUMENTOS ANEXOS" in table_text.upper():
                        # Obtener filas de esta tabla
                        anexo_rows = await table.query_selector_all("tr")
                        for arow in anexo_rows:
                            acells = await arow.query_selector_all("td")
                            if len(acells) >= 1:
                                nombre_archivo = (await acells[0].inner_text()).strip()
                                # Filtrar headers y textos no deseados
                                if nombre_archivo and \
                                   "Descripción" not in nombre_archivo and \
                                   "ARCHIVO PARA" not in nombre_archivo.upper() and \
                                   len(nombre_archivo) > 3:
                                    anexos.append({
                                        "nombre": nombre_archivo,
                                        "url": url
                                    })
                                    print(f"✓ Anexo encontrado: {nombre_archivo}")
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
            
            print(f"✓ RUC {ruc}: {len(items)} items, Total: {total_general}, Anexos: {len(anexos)}")
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