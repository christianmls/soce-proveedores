from playwright.async_api import async_playwright
import re
from typing import Dict, Optional
import asyncio

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
        # Remover todo excepto dígitos y punto decimal
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
            
            # 1. LOCALIZAR TOTAL - Mejorado
            total_general = 0.0
            try:
                # Buscar la fila que contiene "TOTAL:"
                total_row = page.locator("tr:has-text('TOTAL:')")
                
                # El total está en la celda que tiene el valor numérico seguido de "USD"
                # Buscar todas las celdas de esa fila
                cells = await total_row.locator("td").all()
                
                # Recorrer las celdas buscando el valor
                for cell in cells:
                    text = await cell.inner_text()
                    # Si contiene números y no es solo texto
                    if re.search(r'\d', text) and 'TOTAL' not in text.upper():
                        # Intentar extraer el número
                        valor = clean_val(text)
                        if valor > 0:
                            total_general = valor
                            print(f"Total encontrado para RUC {ruc}: {total_general}")
                            break
                
                # Si no se encontró así, intentar con el método anterior
                if total_general == 0.0:
                    total_text = await total_row.locator("td").nth(-2).inner_text()
                    total_general = clean_val(total_text)
                    print(f"Total encontrado (método alternativo) para RUC {ruc}: {total_general}")
                    
            except Exception as e:
                print(f"Error extrayendo total para RUC {ruc}: {str(e)}")
                # Intentar buscar el total en todo el contenido de la página
                try:
                    content = await page.content()
                    # Buscar patrón TOTAL: seguido de número
                    match = re.search(r'TOTAL[:\s]+(?:USD\.?)?[\s]*([\d.,]+)', content, re.IGNORECASE)
                    if match:
                        total_general = clean_val(match.group(1))
                        print(f"Total encontrado por regex para RUC {ruc}: {total_general}")
                except:
                    pass

            # 2. PRODUCTOS
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 8:
                    txt = await row.inner_text()
                    if "TOTAL" in txt.upper() or "DESCRIPCIÓN" in txt.upper() or "No." in txt: 
                        continue
                    try:
                        # Extraer valores de las celdas
                        numero = (await cells[0].inner_text()).strip()
                        cpc = (await cells[1].inner_text()).strip()
                        desc_cell3 = (await cells[3].inner_text()).strip()
                        unid = (await cells[4].inner_text()).strip()
                        cant = clean_val(await cells[5].inner_text())
                        v_unit = clean_val(await cells[6].inner_text())
                        v_tot = clean_val(await cells[7].inner_text())
                        
                        # Solo agregar si tiene número de item válido
                        if numero and numero.isdigit():
                            items.append({
                                "numero": numero,
                                "cpc": cpc,
                                "desc": f"[{cpc}] {desc_cell3}",
                                "unid": unid,
                                "cant": cant,
                                "v_unit": v_unit,
                                "v_tot": v_tot
                            })
                            print(f"Item {numero}: {v_tot}")
                    except Exception as e:
                        print(f"Error extrayendo item: {e}")
                        continue

            # Si el total no se encontró, sumarlo de los items
            if total_general == 0.0 and items:
                total_general = sum(item['v_tot'] for item in items)
                print(f"Total calculado de items para RUC {ruc}: {total_general}")

            # 3. ANEXOS
            anexos = []
            anexo_btns = await page.query_selector_all("input[type='image']")
            for btn in anexo_btns:
                try:
                    fila = await btn.evaluate_handle("el => el.closest('tr')")
                    celdas = await fila.query_selector_all("td")
                    if celdas:
                        nombre = (await celdas[0].inner_text()).strip()
                        if nombre and "Archivo" not in nombre and "ARCHIVO" not in nombre.upper():
                            anexos.append({"nombre": nombre, "url": url})
                except: 
                    continue

            # Cerrar limpiamente
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
            
            resultado = {"total": total_general, "items": items, "anexos": anexos}
            print(f"Resultado final para RUC {ruc}: {resultado}")
            
            return resultado
            
    except Exception as e:
        print(f"Error en scraping RUC {ruc}: {str(e)}")
        # Cerrar recursos en caso de error
        try:
            if page:
                await page.close()
        except:
            pass
        try:
            if context:
                await context.close()
        except:
            pass
        try:
            if browser:
                await browser.close()
        except:
            pass
        return None