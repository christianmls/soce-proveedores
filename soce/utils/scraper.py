from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    """
    Scraper optimizado para la proforma del SERCOP.
    Captura ítems (9 columnas), Anexos y Total General.
    """
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    browser = None
    
    def clean_val(txt: str) -> float:
        if not txt: return 0.0
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
            
            # 1. CAPTURA DEL TOTAL GENERAL
            total_general = 0.0
            try:
                # Buscamos la celda que sigue al texto 'TOTAL:'
                total_text = await page.locator("td:has-text('TOTAL:') + td").inner_text()
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

            # 3. EXTRACCIÓN DE ÍTEMS (Índices corregidos para 9 columnas)
            items = []
            rows = await page.query_selector_all("table tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                # La tabla real tiene 8 o 9 celdas por el desfase de CPC y Moneda
                if len(cells) >= 8:
                    txt_fila = await row.inner_text()
                    if "TOTAL" in txt_fila or "Descripción" in txt_fila or "No." in txt_fila:
                        continue
                    try:
                        # Mapeo según estructura real del sitio:
                        # 0:No | 1:CPC-Cod | 2:CPC-Desc | 3:Prod-Desc | 4:Unid | 5:Cant | 6:VUnit | 7:VTot
                        items.append({
                            "numero": (await cells[0].inner_text()).strip(),
                            "cpc": (await cells[1].inner_text()).strip(),
                            "cpc_descripcion": (await cells[2].inner_text()).strip(),
                            "descripcion": (await cells[3].inner_text()).strip(),
                            "unidad": (await cells[4].inner_text()).strip(),
                            "cantidad": clean_val(await cells[5].inner_text()),
                            "v_unit": clean_val(await cells[6].inner_text()),
                            "v_total": clean_val(await cells[7].inner_text())
                        })
                    except: continue

            # 4. SCRAPPING DE ARCHIVOS ANEXOS
            anexos = []
            # Buscamos en la sección de anexos específicamente
            iconos_anexos = await page.query_selector_all("input[type='image'], img[src*='descargar']")
            for icono in iconos_anexos:
                try:
                    # Obtenemos la fila que contiene el icono
                    fila_anexo = await icono.evaluate_handle("el => el.closest('tr')")
                    celdas_anexo = await fila_anexo.query_selector_all("td")
                    if celdas_anexo:
                        nombre_doc = (await celdas_anexo[0].inner_text()).strip()
                        # Si no tiene nombre claro, es un header o basura
                        if nombre_doc and "Descripción" not in nombre_doc:
                            anexos.append({
                                "nombre": nombre_doc,
                                "url": url # Usamos la URL base como referencia de descarga
                            })
                except: continue

            await browser.close()
            return {
                "razon_social": razon_social, 
                "total_general": total_general,
                "items": items, 
                "anexos": anexos
            }
    except Exception as e:
        print(f"DEBUG ERROR SCRAPER: {e}")
        if browser: await browser.close()
        return None