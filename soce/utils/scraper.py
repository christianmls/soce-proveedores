from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    browser = None
    
    def clean_float(txt: str) -> float:
        if not txt: return 0.0
        # Elimina "USD.", comas y cualquier letra para dejar solo números y punto
        clean = re.sub(r'[^\d\.]', '', txt.replace(',', ''))
        try:
            return float(clean) if clean else 0.0
        except:
            return 0.0

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3500)
            
            # Validación de Proforma
            try:
                total_text = await page.locator("td:has-text('TOTAL:') + td").inner_text()
                total_val = clean_float(total_text)
                if total_val <= 0:
                    await browser.close()
                    return None
            except:
                await browser.close()
                return None

            # Razón Social
            texto_completo = await page.inner_text('body')
            razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', texto_completo)
            razon_social = razon_match.group(1).strip() if razon_match else "N/D"

            # Extracción de ítems (Blindada contra "USD.")
            items = []
            rows = await page.query_selector_all("table tr")
            for i, row in enumerate(rows):
                cells = await row.query_selector_all("td")
                if len(cells) >= 7:
                    txt = await row.inner_text()
                    if "TOTAL" in txt or "Descripción" in txt or "No." in txt:
                        continue
                    
                    try:
                        # Extraemos los datos usando el helper clean_float
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "descripcion": (await cells[2].inner_text()).strip(),
                            "unidad": (await cells[3].inner_text()).strip(),
                            "cantidad": clean_float(await cells[4].inner_text()),
                            "v_unit": clean_float(await cells[5].inner_text()),
                            "v_total": clean_float(await cells[6].inner_text())
                        })
                    except Exception as e:
                        print(f"DEBUG: Error fila {i}: {e}")
            
            # Extracción de anexos
            anexos = []
            iconos = await page.query_selector_all("input[type='image'], img[src*='descargar']")
            for icono in iconos:
                try:
                    fila = await icono.evaluate_handle("el => el.closest('tr')")
                    celdas = await fila.query_selector_all("td")
                    if celdas:
                        nombre = (await celdas[0].inner_text()).strip()
                        if nombre and "Archivo" not in nombre:
                            anexos.append({"nombre": nombre, "url": url})
                except: continue
            
            await browser.close()
            return {"razon_social": razon_social, "items": items, "anexos": anexos}
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        if browser: await browser.close()
        return None