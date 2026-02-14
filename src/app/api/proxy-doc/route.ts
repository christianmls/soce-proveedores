import { NextRequest, NextResponse } from 'next/server'

const ALLOWED_HOST = 'www.compraspublicas.gob.ec'

/** Detecta el Content-Type real leyendo los magic bytes del contenido */
function detectContentType(buffer: ArrayBuffer): { mime: string; ext: string } {
  const bytes = new Uint8Array(buffer.slice(0, 8))
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
  const ascii = String.fromCharCode(...bytes.slice(0, 5))

  if (ascii.startsWith('%PDF')) return { mime: 'application/pdf', ext: 'pdf' }
  if (hex.startsWith('504b0304')) return { mime: 'application/zip', ext: 'zip' } // .docx/.xlsx/zip
  if (hex.startsWith('d0cf11e0')) return { mime: 'application/msword', ext: 'doc' } // .doc/.xls
  if (hex.startsWith('ffd8ff')) return { mime: 'image/jpeg', ext: 'jpg' }
  if (hex.startsWith('89504e47')) return { mime: 'image/png', ext: 'png' }

  return { mime: 'application/octet-stream', ext: 'bin' }
}

/** Extrae el filename del header Content-Disposition del servidor upstream */
function extractFilename(disposition: string | null): string | null {
  if (!disposition) return null
  const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';\r\n]+)["']?/i)
  return match ? decodeURIComponent(match[1].trim()) : null
}

export async function GET(request: NextRequest) {
  const url = request.nextUrl.searchParams.get('url')

  if (!url) {
    return new NextResponse('Falta parámetro url', { status: 400 })
  }

  let parsed: URL
  try {
    parsed = new URL(url)
  } catch {
    return new NextResponse('URL inválida', { status: 400 })
  }

  if (parsed.hostname !== ALLOWED_HOST) {
    return new NextResponse('Dominio no permitido', { status: 403 })
  }

  try {
    const upstream = await fetch(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        Accept: 'application/pdf,*/*',
      },
    })

    if (!upstream.ok) {
      return new NextResponse('Error al obtener el documento', { status: upstream.status })
    }

    const body = await upstream.arrayBuffer()

    // Detectar tipo real por magic bytes (el servidor puede devolver octet-stream)
    const { mime, ext } = detectContentType(body)

    // Intentar obtener el nombre del archivo del servidor upstream
    const upstreamFilename = extractFilename(upstream.headers.get('content-disposition'))
    const filename = upstreamFilename ?? `documento.${ext}`

    return new NextResponse(body, {
      headers: {
        'Content-Type': mime,
        'Content-Disposition': `inline; filename="${filename}"`,
        // Expone el MIME detectado para que el cliente decida cómo renderizar
        'X-File-Mime': mime,
        'Cache-Control': 'public, max-age=300',
      },
    })
  } catch {
    return new NextResponse('Error interno al obtener el documento', { status: 500 })
  }
}
