from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
        # Extrae solo números y punto decimal, ignorando "USD.", comas, etc.
        clean = re.sub(r'[^\d\.]', '', txt.replace(',', ''))
        try:
            return float(clean) if clean else 0.0
        except: return 0.0

    browser = None
    try:
        async with async_playwright() as p:
            # Flags extra para estabilidad en Docker y evitar EPIPE
            browser = await p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-setuid-sandbox']
            )
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            await page.wait_for_timeout(4000)
            
            # 1. VALIDACIÓN DEL TOTAL (Si es 0, descartamos proforma)
            total_gen = 0.0
            try:
                total_text = await page.locator("td:has-text('TOTAL:') + td").inner_text()
                total_gen = clean_val(total_text)
                if total_gen <= 0:
                    print(f"DEBUG: Total {total_gen} es cero. Saltando.")
                    await browser.close()
                    return None
            except:
                await browser.close()
                return None

            # 2. DATOS PROVEEDOR
            texto_completo = await page.inner_text('body')
            razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', texto_completo)
            razon_social = razon_match.group(1).strip() if razon_match else "N/D"

            # 3. EXTRACCIÓN DE ÍTEMS (Mapeo corregido por desfase de CPC)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 7:
                    txt_fila = await row.inner_text()
                    if "TOTAL" in txt_fila or "Descripción" in txt_fila or "No." in txt_fila:
                        continue
                    try:
                        # Web SERCOP 9 celdas: 0:No, 1:CPC_Cod, 2:CPC_Txt, 3:Prod_Desc, 4:Unid, 5:Cant, 6:VUnit, 7:VTot, 8:USD
                        # Ajustamos índices para capturar Cantidad y V. Unitario correctamente
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "cpc_desc": (await cells[2].inner_text()).strip(),
                            "descripcion": (await cells[3].inner_text()).strip(),
                            "unidad": (await cells[4].inner_text()).strip(),
                            "cantidad": clean_val(await cells[5].inner_text()),
                            "v_unit": clean_val(await cells[6].inner_text()),
                            "v_total": clean_val(await cells[7].inner_text())
                        })
                    except: continue

            # 4. EXTRACCIÓN DE ANEXOS (Detección de iconos de disquete)
            anexos = []
            anexo_rows = await page.query_selector_all("tr:has(input[type='image'])")
            for a_row in anexo_rows:
                a_cells = await a_row.query_selector_all("td")
                btn = await a_row.query_selector("input[type='image']")
                if len(a_cells) >= 1 and btn:
                    nombre_doc = (await a_cells[0].inner_text()).strip()
                    # Si no tiene nombre claro, es basura
                    if nombre_doc and "Archivo" not in nombre_doc:
                        anexos.append({"nombre": nombre_doc, "url": url})

            print(f"DEBUG: Finalizado {ruc} | Items: {len(items)} | Anexos: {len(anexos)}")
            await browser.close()
            return {"razon_social": razon_social, "items": items, "anexos": anexos}
    except Exception as e:
        print(f"DEBUG ERROR SCRAPER: {e}")
        if browser: await browser.close()
        return None