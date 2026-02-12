from playwright.async_api import async_playwright
import re
from typing import Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
        clean = re.sub(r'[^\d\.]', '', txt.replace(',', ''))
        try: return float(clean) if clean else 0.0
        except: return 0.0

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-setuid-sandbox']
            )
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(4000)
            
            # 1. TOTAL GENERAL (Ubicado en el 2do tbody)
            total_general = 0.0
            try:
                # Localizamos la fila que contiene "TOTAL:" sin importar el tbody
                total_row = page.locator("tr:has-text('TOTAL:')")
                total_text = await total_row.locator("td").last.inner_text()
                total_general = clean_val(total_text)
            except: pass

            # 2. ÍTEMS (Estructura de 9 columnas)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 8:
                    txt = await row.inner_text()
                    if "TOTAL" in txt or "Descripción" in txt or "No." in txt: continue
                    try:
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "desc": f"[{ (await cells[1].inner_text()).strip() }] {(await cells[3].inner_text()).strip()}",
                            "unid": (await cells[4].inner_text()).strip(),
                            "cant": clean_val(await cells[5].inner_text()),
                            "v_unit": clean_val(await cells[6].inner_text()),
                            "v_tot": clean_val(await cells[7].inner_text())
                        })
                    except: continue

            # 3. ANEXOS (Botones de tipo imagen)
            anexos = []
            anexo_btns = await page.query_selector_all("input[type='image']")
            for btn in anexo_btns:
                try:
                    fila = await btn.evaluate_handle("el => el.closest('tr')")
                    celdas = await fila.query_selector_all("td")
                    if celdas:
                        nombre = (await celdas[0].inner_text()).strip()
                        if nombre and "Archivo" not in nombre and "Descripción" not in nombre:
                            anexos.append({"nombre": nombre, "url": url})
                except: continue

            await browser.close()
            if not items and total_general <= 0: return None
            return {"total": total_general, "items": items, "anexos": anexos}
    except:
        if browser: await browser.close()
        return None