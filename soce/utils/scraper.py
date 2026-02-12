from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import re
from typing import List, Dict, Optional

async def scrape_proceso(proceso_id: str, ruc: str) -> Optional[Dict]:
    pid_clean = proceso_id.rstrip(',')
    url = f"https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id={pid_clean}&ruc={ruc}"
    
    print(f"--- DEBUG: Iniciando scrap para RUC {ruc} ---")
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(4000) # Un segundo extra para carga de tablas
            
            # 1. VALIDACIÓN DE TOTAL
            total_val = 0.0
            try:
                # Selector más flexible para el Total
                total_element = page.locator("td:has-text('TOTAL:'), td:has-text('Total:')").locator("xpath=following-sibling::td[1]")
                total_text = await total_element.first.inner_text()
                total_val = float(re.sub(r'[^\d\.]', '', total_text.replace(',', '')))
                print(f"DEBUG: Total detectado: {total_val}")
                if total_val <= 0:
                    print("DEBUG: Total es 0. Oferta inválida.")
                    await browser.close()
                    return None
            except Exception as e:
                print(f"DEBUG: Error al buscar Total: {e}")
                await browser.close()
                return None

            # 2. DATOS PROVEEDOR
            texto_completo = await page.inner_text('body')
            razon_match = re.search(r'Razón Social[:\s]+([^\n]+)', texto_completo)
            razon_social = razon_match.group(1).strip() if razon_match else "N/D"
            print(f"DEBUG: Razón Social: {razon_social}")

            # 3. EXTRACCIÓN DE ÍTEMS
            items = []
            # Buscamos todas las tablas y filtramos la que tiene los productos
            tablas = await page.query_selector_all("table")
            for tabla in tablas:
                header_text = await tabla.inner_text()
                if "Descripción del Producto" not in header_text:
                    continue
                
                filas = await tabla.query_selector_all("tr")
                for fila in filas:
                    celdas = await fila.query_selector_all("td")
                    if len(celdas) >= 7:
                        # La primera celda suele ser el número (1, 2, 3...)
                        num_text = (await celdas[0].inner_text()).strip()
                        if num_text.isdigit():
                            try:
                                items.append({
                                    "numero": num_text,
                                    "cpc": (await celdas[1].inner_text()).strip().split('\n')[0],
                                    "descripcion": (await celdas[2].inner_text()).strip(),
                                    "unidad": (await celdas[3].inner_text()).strip(),
                                    "cantidad": float(re.sub(r'[^\d\.]', '', (await celdas[4].inner_text()).replace(',', ''))),
                                    "v_unit": float(re.sub(r'[^\d\.]', '', (await celdas[5].inner_text()).replace(',', ''))),
                                    "v_total": float(re.sub(r'[^\d\.]', '', (await celdas[6].inner_text()).replace(',', '')))
                                })
                            except Exception as e:
                                print(f"DEBUG: Error parseando fila {num_text}: {e}")
            
            print(f"DEBUG: Items encontrados: {len(items)}")

            # 4. ANEXOS
            anexos = []
            # Buscamos directamente todos los botones de descarga (inputs de imagen)
            botones_anexos = await page.query_selector_all("input[type='image']")
            for btn in botones_anexos:
                # Subimos al nivel de la fila para obtener la descripción
                fila_anexo = await btn.evaluate_handle("el => el.closest('tr')")
                celdas_anexo = await fila_anexo.query_selector_all("td")
                if celdas_anexo:
                    nombre = (await celdas_anexo[0].inner_text()).strip()
                    link = await btn.get_attribute("src") or url
                    # Filtramos que no sea un icono genérico del sistema
                    if nombre and len(nombre) > 3 and "TOTAL" not in nombre.upper():
                        anexos.append({"nombre": nombre, "url": link})
            
            print(f"DEBUG: Anexos encontrados: {len(anexos)}")

            await browser.close()
            return {"razon_social": razon_social, "items": items, "anexos": anexos}
    except Exception as e:
        print(f"DEBUG ERROR CRITICAL: {e}")
        if browser: await browser.close()
        return None