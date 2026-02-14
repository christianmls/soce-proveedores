import { chromium, Browser, BrowserContext, Page } from 'playwright'

interface DatosProveedor {
  ruc: string
  razonSocial: string
  correo: string
  telefono: string
  pais: string
  provincia: string
  canton: string
  direccion: string
}

interface Item {
  numero: string
  cpc: string
  desc: string
  unid: string
  cant: number
  v_unit: number
  v_tot: number
}

interface Anexo {
  nombre: string
  url: string
}

interface ResultadoScraping {
  total: number
  items: Item[]
  anexos: Anexo[]
  proveedor: DatosProveedor
  nic: string
}

function cleanVal(txt: string): number {
  if (!txt) return 0.0
  let clean = txt.replace(/USD/g, '').replace(/Unidad/g, '').trim()
  clean = clean.replace(/[^\d.]/g, '')
  try {
    return clean ? parseFloat(clean) : 0.0
  } catch {
    return 0.0
  }
}

export async function scrapeProceso(
  procesoId: string,
  ruc: string
): Promise<ResultadoScraping | null> {
  const pidClean = procesoId.replace(/,+$/, '')
  const url = `https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/FrmNCOProformaRegistrada.cpe?id=${pidClean}&ruc=${ruc}`

  let browser: Browser | null = null
  let context: BrowserContext | null = null
  let page: Page | null = null

  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-setuid-sandbox'],
    })

    context = await browser.newContext()
    page = await context.newPage()

    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.waitForTimeout(4000)

    let totalGeneral = 0.0
    const items: Item[] = []
    const anexos: Anexo[] = []
    const datosProveedor: DatosProveedor = {
      ruc,
      razonSocial: '',
      correo: '',
      telefono: '',
      pais: '',
      provincia: '',
      canton: '',
      direccion: '',
    }

    // ===== EXTRAER DATOS DEL PROVEEDOR =====
    try {
      const extracted = await page.evaluate(() => {
        /**
         * Busca el valor asociado a un label. Estrategias en orden:
         * 1. td/th que contiene el label → siguiente td hermano en la misma fila
         * 2. Elemento hoja que contiene el label → siguiente elemento hermano
         * 3. El propio elemento contiene "Label: Valor" → extrae tras el colon
         * 4. Regex sobre el texto completo del body como último recurso
         */
        function findValue(labels: string[], maxLen = 150): string {
          const norm = (s: string) =>
            s
              .normalize('NFD')
              .replace(/[\u0300-\u036f]/g, '')
              .replace(/\s+/g, ' ')
              .toLowerCase()
              .trim()

          const labelNorms = labels.map(norm)

          // Solo coincide si el texto es esencialmente el label (celda etiqueta pura)
          // Se permiten hasta 8 chars extra por colon, espacios e icono
          const isPureLabel = (text: string): boolean => {
            const n = norm(text)
            return labelNorms.some((lbl) => n.includes(lbl) && n.length <= lbl.length + 8)
          }

          // Un valor es válido si no está vacío y no es demasiado largo
          const isOk = (val: string): boolean => val.length > 0 && val.length <= maxLen

          // ── Estrategia 1: celda de tabla que sea puro label ───────────────
          const cells = Array.from(document.querySelectorAll('td, th'))
          for (const cell of cells) {
            const cellText = cell.textContent?.trim() ?? ''
            if (!isPureLabel(cellText)) continue

            // 1a: siguiente td en la misma fila
            const row = cell.closest('tr')
            if (row) {
              const rowCells = Array.from(row.querySelectorAll('td, th'))
              const idx = rowCells.indexOf(cell as HTMLTableCellElement)
              if (idx !== -1 && idx + 1 < rowCells.length) {
                const val = rowCells[idx + 1].textContent?.trim() ?? ''
                if (isOk(val)) return val
              }
            }

            // 1b: hermano directo td/th
            const next = cell.nextElementSibling
            if (next && (next.tagName === 'TD' || next.tagName === 'TH')) {
              const val = next.textContent?.trim() ?? ''
              if (isOk(val)) return val
            }
          }

          // ── Estrategia 2: elemento hoja (span, b, strong…) puro label ─────
          const leafTags = ['span', 'b', 'strong', 'em', 'label', 'font']
          const leaves = Array.from(document.querySelectorAll(leafTags.join(',')))
          for (const el of leaves) {
            if (el.children.length > 0) continue
            const text = el.textContent?.trim() ?? ''
            if (!isPureLabel(text)) continue

            // 2a: hermano inmediato
            const next = el.nextElementSibling
            if (next) {
              const val = next.textContent?.trim() ?? ''
              if (isOk(val)) return val
            }

            // 2b: siguiente hermano del padre
            const parent = el.parentElement
            if (parent) {
              const parentNext = parent.nextElementSibling
              if (parentNext) {
                const val = parentNext.textContent?.trim() ?? ''
                if (isOk(val)) return val
              }
            }
          }

          // ── Estrategia 3: body.innerText – preservar saltos de línea ──────
          // Solo normalizar espacios/tabs dentro de cada línea, NO los \n
          const bodyText = (document.body.innerText ?? '').replace(/[ \t]+/g, ' ')

          // Patrón para cortar el valor antes del siguiente label conocido
          const stopRe =
            /Raz[oó]n\s+Social|Correo\s+electr[oó]nico|Tel[eé]fono|Pa[íi]s|Provincia|Cant[oó]n|Direcci[oó]n/i

          for (const lbl of labels) {
            const escaped = lbl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
            // Captura hasta fin de línea (los \n ya están preservados)
            const re = new RegExp(escaped + '\\s*:?\\s*([^\\n\\r]+)', 'i')
            const m = bodyText.match(re)
            if (m) {
              let val = m[1].trim()
              // Recortar si aparece otro label en la misma línea
              const cut = val.search(stopRe)
              if (cut > 0) val = val.substring(0, cut).trim()
              if (isOk(val)) return val
            }
          }

          return ''
        }

        return {
          razonSocial: findValue(['Razón Social', 'Razon Social']),
          correo: findValue(['Correo electrónico', 'Correo electronico', 'Correo Electrónico']),
          telefono: findValue(['Teléfono', 'Telefono']),
          pais: findValue(['País', 'Pais']),
          provincia: findValue(['Provincia']),
          canton: findValue(['Cantón', 'Canton']),
          direccion: findValue(['Dirección', 'Direccion']),
        }
      })

      datosProveedor.razonSocial = extracted.razonSocial
      datosProveedor.correo = extracted.correo
      datosProveedor.telefono = extracted.telefono
      datosProveedor.pais = extracted.pais
      datosProveedor.provincia = extracted.provincia
      datosProveedor.canton = extracted.canton
      datosProveedor.direccion = extracted.direccion

      console.log(`✓ Proveedor: ${datosProveedor.razonSocial} (${datosProveedor.ruc})`)
      console.log(`  Correo: ${datosProveedor.correo}`)
      console.log(`  Tel: ${datosProveedor.telefono}`)
      console.log(`  País/Prov/Cantón: ${datosProveedor.pais} / ${datosProveedor.provincia} / ${datosProveedor.canton}`)
      console.log(`  Dirección: ${datosProveedor.direccion}`)
    } catch (e) {
      console.error('Error extrayendo datos del proveedor:', e)
    }

    // ===== EXTRAER NIC DEL BREADCRUMB =====
    let nic = ''
    try {
      nic = await page.evaluate(() => {
        const text = document.body.innerText ?? ''
        const m = text.match(/NIC-\d{5,}-\d{4}-\d+/)
        return m ? m[0] : ''
      })
      if (nic) console.log(`✓ NIC: ${nic}`)
    } catch (e) {
      console.error('Error extrayendo NIC:', e)
    }

    // ===== EXTRAER ITEMS Y TOTAL =====
    const rows = await page.locator('table tr').all()

    for (const row of rows) {
      const cells = await row.locator('td').all()
      const rowText = await row.innerText()

      if (rowText.toUpperCase().includes('TOTAL:') && rowText.includes('**')) {
        const totalMatch = rowText.match(/\*\*(\d+\.?\d*)\*\*/)
        if (totalMatch) {
          totalGeneral = parseFloat(totalMatch[1])
          console.log(`✓ Total: ${totalGeneral}`)
        }
        continue
      }

      if (cells.length === 9) {
        try {
          const numero = (await cells[0].innerText()).trim()

          if (numero && /^\d+$/.test(numero)) {
            const cpc = (await cells[1].innerText()).trim()
            const nombreProducto = (await cells[2].innerText()).trim()
            const descripcion = (await cells[3].innerText()).trim()
            const unidad = (await cells[4].innerText()).trim()
            const cantidad = cleanVal(await cells[5].innerText())
            const vUnitario = cleanVal(await cells[6].innerText())
            const vTotal = cleanVal(await cells[7].innerText())

            items.push({
              numero,
              cpc,
              desc: `[${cpc}] ${nombreProducto} - ${descripcion}`,
              unid: unidad,
              cant: cantidad,
              v_unit: vUnitario,
              v_tot: vTotal,
            })

            console.log(`✓ Item ${numero}: $${vTotal}`)
          }
        } catch {
          continue
        }
      }
    }

    // Si el total no se detectó por la fila de totales, calcularlo desde los items
    if (totalGeneral === 0 && items.length > 0) {
      totalGeneral = items.reduce((sum, item) => sum + item.v_tot, 0)
      console.log(`✓ Total (calculado de items): ${totalGeneral}`)
    }

    // ===== EXTRAER ANEXOS =====
    try {
      const anexosEncontrados = await page.evaluate(() => {
        const INVALID = [
          'descripción del archivo',
          'descargar archivo',
          'archivo para adjuntar',
          'descripción',
        ]

        const results: Array<{ nombre: string; url: string }> = []
        const seen = new Set<string>()

        // Selector amplio: cualquier <a> cuyo href contenga el endpoint de descarga
        const links = Array.from(
          document.querySelectorAll<HTMLAnchorElement>('a[href*="ExeGENBajarArchivoGeneral"]')
        )

        for (const link of links) {
          const url = link.href // el navegador ya lo resuelve como URL absoluta
          if (!url) continue

          // Buscar el nombre del archivo en la misma fila de tabla
          const row = link.closest('tr')
          if (!row) continue

          let nombre = ''
          const cells = Array.from(row.querySelectorAll('td, th'))

          for (const cell of cells) {
            // Ignorar la celda que contiene el propio link de descarga
            if (cell.contains(link)) continue
            const text = cell.textContent?.replace(/\s+/g, ' ').trim() ?? ''
            if (text.length > 2) {
              nombre = text
              break
            }
          }

          if (!nombre) continue

          const low = nombre.toLowerCase()
          const esValido = !INVALID.some((inv) => low.includes(inv))

          if (esValido && !seen.has(nombre)) {
            seen.add(nombre)
            results.push({ nombre, url })
          }
        }

        return results
      })

      for (const a of anexosEncontrados) {
        anexos.push({ nombre: a.nombre, url: a.url })
        console.log(`✓ Anexo: ${a.nombre}`)
      }
    } catch (e) {
      console.error('Error extrayendo anexos:', e)
    }

    // Cerrar navegador
    if (page) await page.close()
    if (context) await context.close()
    if (browser) await browser.close()

    const resultado: ResultadoScraping = {
      total: totalGeneral,
      items,
      anexos,
      proveedor: datosProveedor,
      nic,
    }

    console.log(
      `✅ RUC ${ruc}: ${items.length} items, Total=$${totalGeneral}, ${anexos.length} anexos`
    )
    return resultado
  } catch (e) {
    console.error(`❌ Error scraping RUC ${ruc}:`, e)
    try {
      if (page) await page.close()
      if (context) await context.close()
      if (browser) await browser.close()
    } catch {
      // ignore
    }
    return null
  }
}
