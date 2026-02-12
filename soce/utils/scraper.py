from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
        # Elimina USD, comas y deja solo números y punto
        clean = re.sub(r'[^\d\.]', '', txt.replace(',', ''))
        try:
            return float(clean) if clean else 0.0
        except:
            return 0.0

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3500)
            
            # Validación: Total > 0
            try:
                total_text = await page.locator("td:has-text('TOTAL:') + td").inner_text()
                if clean_val(total_text) <= 0:
                    await browser.close()
                    return None
            except:
                await browser.close()
                return None

            # Razón Social
            texto = await page.inner_text('body')
            razon = re.search(r'Razón Social[:\s]+([^\n]+)', texto)
            razon_social = razon.group(1).strip() if razon else "N/D"

            # Ítems (1-7)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 7:
                    txt_fila = await row.inner_text()
                    if "TOTAL" in txt_fila or "Descripción" in txt_fila or "No." in txt_fila:
                        continue
                    try:
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "descripcion": (await cells[2].inner_text()).strip(),
                            "unidad": (await cells[3].inner_text()).strip(),
                            "cantidad": clean_val(await cells[4].inner_text()),
                            "v_unit": clean_val(await cells[5].inner_text()),
                            "v_total": clean_val(await cells[6].inner_text())
                        })
                    except: continue

            # Anexos
            anexos = []
            iconos = await page.query_selector_all("input[type='image'], img[src*='descargar']")
            for icono in iconos:
                try:
                    fila = await icono.evaluate_handle("el => el.closest('tr')")
                    celdas = await fila.query_selector_all("td")
                    if celdas:
                        nombre = (await celdas[0].inner_text()).strip()
                        link = await icono.get_attribute("src") or url
                        if nombre and "Archivo" not in nombre:
                            anexos.append({"nombre": nombre, "url": link})
                except: continue

            await browser.close()
            return {"razon_social": razon_social, "items": items, "anexos": anexos}
    except Exception:
        if browser: await browser.close()
        return None