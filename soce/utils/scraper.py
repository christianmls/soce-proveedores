from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 1. VALIDACIÓN DE TOTAL (Si es 0 o no existe, descartamos)
            total_val = 0.0
            try:
                total_text = await page.locator("text='TOTAL:'").locator("xpath=following-sibling::td[1]").inner_text()
                total_val = float(re.sub(r'[^\d\.]', '', total_text.replace(',', '')))
            except: pass
            
            if total_val <= 0:
                await browser.close()
                return None

            # 2. DATOS PROVEEDOR
            texto_completo = await page.inner_text('body')
            razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', texto_completo)
            razon_social = razon_match.group(1).strip() if razon_match else "N/D"

            # 3. ÍTEMS (Col 1 a 7)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 7:
                    txt = await row.inner_text()
                    if "TOTAL" in txt or "Descripción" in txt: continue
                    try:
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "descripcion": (await cells[2].inner_text()).strip(),
                            "unidad": (await cells[3].inner_text()).strip(),
                            "cantidad": float(re.sub(r'[^\d\.]', '', (await cells[4].inner_text()).replace(',', ''))),
                            "v_unit": float(re.sub(r'[^\d\.]', '', (await cells[5].inner_text()).replace(',', ''))),
                            "v_total": float(re.sub(r'[^\d\.]', '', (await cells[6].inner_text()).replace(',', '')))
                        })
                    except: continue

            # 4. ANEXOS
            anexos = []
            anexo_rows = await page.query_selector_all("tr:has(input[type='image'])")
            for a_row in anexo_rows:
                a_cells = await a_row.query_selector_all("td")
                if len(a_cells) >= 1:
                    nombre = (await a_cells[0].inner_text()).strip()
                    if nombre and "Archivo" not in nombre:
                        anexos.append(nombre)

            await browser.close()
            return {"razon_social": razon_social, "items": items, "anexos": anexos}
    except Exception:
        if browser: await browser.close()
        return None