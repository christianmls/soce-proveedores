from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
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
            
            # 1. CAPTURA DEL TOTAL GENERAL
            total_general = 0.0
            try:
                total_element = page.locator("td:has-text('TOTAL:') + td")
                total_text = await total_element.inner_text()
                total_general = clean_val(total_text)
                if total_general <= 0:
                    await browser.close()
                    return None
            except:
                await browser.close()
                return None

            # 2. DATOS PROVEEDOR
            texto_completo = await page.inner_text('body')
            razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', texto_completo)
            razon_social = razon_match.group(1).strip() if razon_match else "N/D"

            # 3. ÍTEMS (Índices corregidos para 9 columnas por desfase de CPC)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 8:
                    txt_fila = await row.inner_text()
                    if "TOTAL" in txt_fila or "Descripción" in txt_fila or "No." in txt_fila:
                        continue
                    try:
                        # Mapeo real del DOM del SERCOP:
                        # 0:No | 1:CPC Code | 2:CPC Desc | 3:Prod Desc | 4:Unid | 5:Cant | 6:VUnit | 7:VTot
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "descripcion": (await cells[3].inner_text()).strip(), # Usamos la desc del producto
                            "unidad": (await cells[4].inner_text()).strip(),
                            "cantidad": clean_val(await cells[5].inner_text()),
                            "v_unit": clean_val(await cells[6].inner_text()),
                            "v_total": clean_val(await cells[7].inner_text())
                        })
                    except: continue

            # 4. ANEXOS
            anexos = []
            anexo_rows = await page.query_selector_all("tr:has(input[type='image'])")
            for a_row in anexo_rows:
                a_cells = await a_row.query_selector_all("td")
                btn = await a_row.query_selector("input[type='image']")
                if len(a_cells) >= 1 and btn:
                    nombre = (await a_cells[0].inner_text()).strip()
                    link = await btn.get_attribute("src") or url
                    if nombre and "Archivo" not in nombre:
                        anexos.append({"nombre": nombre, "url": link})

            await browser.close()
            return {
                "razon_social": razon_social, 
                "total_general": total_general,
                "items": items, 
                "anexos": anexos
            }
    except Exception:
        if browser: await browser.close()
        return None