'use client'

import { useState } from 'react'
import {
  FileText,
  ExternalLink,
  User,
  Building,
  Mail,
  Phone,
  MapPin,
  Globe,
  Map,
  Download,
  FileX,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Oferta {
  id: number
  numeroItem: string
  descripcionProducto: string
  valorTotal: number
  razonSocial: string
}

interface Anexo {
  id: number
  nombreArchivo: string
  urlArchivo: string
}

interface Proveedor {
  nombre: string
  correo: string
  telefono: string
  pais: string
  provincia: string
  canton: string
  direccion: string
}

interface OfertasTablaProps {
  ruc: string
  ofertas: Oferta[]
  anexos: Anexo[]
  proveedor: Proveedor | null
}

type LoadState = 'idle' | 'loading' | 'preview' | 'no-preview'

const PREVIEWABLE = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp']

export function OfertasTabla({ ruc, ofertas, anexos, proveedor }: OfertasTablaProps) {
  const total = ofertas.reduce((sum, o) => sum + o.valorTotal, 0)
  const razonSocial = proveedor?.nombre || ofertas[0]?.razonSocial || 'N/A'

  const [anexoAbierto, setAnexoAbierto] = useState<Anexo | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('idle')
  const [blobUrl, setBlobUrl] = useState<string | null>(null)

  const abrirAnexo = async (anexo: Anexo) => {
    // Limpiar blob anterior
    if (blobUrl) URL.revokeObjectURL(blobUrl)
    setBlobUrl(null)
    setAnexoAbierto(anexo)
    setLoadState('loading')

    try {
      const res = await fetch(`/api/proxy-doc?url=${encodeURIComponent(anexo.urlArchivo)}`)
      if (!res.ok) throw new Error('Error al obtener el documento')

      // Leer MIME detectado por magic bytes en el proxy
      const mime = (res.headers.get('x-file-mime') ?? res.headers.get('content-type') ?? '')
        .split(';')[0]
        .trim()

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)

      if (PREVIEWABLE.includes(mime)) {
        setBlobUrl(url)
        setLoadState('preview')
      } else {
        // No previsualizable: descargar automáticamente y mostrar mensaje
        const a = document.createElement('a')
        a.href = url
        a.download = anexo.nombreArchivo
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        setTimeout(() => URL.revokeObjectURL(url), 1000)
        setLoadState('no-preview')
      }
    } catch {
      setLoadState('no-preview')
    }
  }

  const cerrarModal = () => {
    if (blobUrl) URL.revokeObjectURL(blobUrl)
    setBlobUrl(null)
    setAnexoAbierto(null)
    setLoadState('idle')
  }

  // Sin oferta: mostrar mensaje simplificado
  if (total === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-green-600">Proveedor RUC: {ruc}</h2>
        <Card>
          <CardContent className="flex items-center gap-3 py-6 text-gray-500">
            <FileX size={20} className="shrink-0 text-gray-400" />
            <span>El proveedor no ha presentado oferta.</span>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-green-600">Proveedor RUC: {ruc}</h2>

      {/* Datos del Proveedor */}
      <Card>
        <CardHeader>
          <CardTitle>Datos del Proveedor</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
            <div className="flex items-center gap-2">
              <User size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">RUC:</span>
              <span>{ruc}</span>
            </div>
            <div className="flex items-center gap-2">
              <Building size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Razón Social:</span>
              <span>{razonSocial}</span>
            </div>
            <div className="flex items-center gap-2">
              <Mail size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Correo electrónico:</span>
              <span>{proveedor?.correo || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Teléfono:</span>
              <span>{proveedor?.telefono || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Globe size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">País:</span>
              <span>{proveedor?.pais || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Map size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Provincia:</span>
              <span>{proveedor?.provincia || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Cantón:</span>
              <span>{proveedor?.canton || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin size={14} className="shrink-0 text-gray-500" />
              <span className="font-bold">Dirección:</span>
              <span>{proveedor?.direccion || 'N/A'}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Ofertas */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60px]">No.</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead className="w-[150px] text-right">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ofertas.map((oferta) => (
              <TableRow key={oferta.id}>
                <TableCell>{oferta.numeroItem}</TableCell>
                <TableCell className="text-sm">{oferta.descripcionProducto}</TableCell>
                <TableCell className="text-right font-mono">
                  {oferta.valorTotal.toFixed(5)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow className="bg-gray-100">
              <TableCell />
              <TableCell className="text-right font-bold">TOTAL:</TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <span className="text-lg font-bold">{total.toFixed(5)}</span>
                  <span className="font-bold">USD.</span>
                </div>
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </Card>

      {/* Anexos */}
      {anexos.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="mb-3 font-bold">Documentos Anexos:</p>
            <div className="flex flex-wrap gap-2">
              {anexos.map((anexo) => (
                <Button
                  key={anexo.id}
                  variant="outline"
                  size="sm"
                  onClick={() => abrirAnexo(anexo)}
                >
                  <FileText size={14} />
                  {anexo.nombreArchivo}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal visor de documento */}
      <Dialog open={!!anexoAbierto} onOpenChange={(open) => !open && cerrarModal()}>
        <DialogContent className="flex h-[90vh] max-w-5xl flex-col gap-0 p-0">
          <DialogHeader className="flex flex-row items-center justify-between border-b px-6 py-3">
            <DialogTitle className="truncate pr-8 text-base">
              {anexoAbierto?.nombreArchivo}
            </DialogTitle>
            <a
              href={anexoAbierto?.urlArchivo}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0"
            >
              <Button variant="ghost" size="sm">
                <ExternalLink size={14} />
                Abrir en pestaña
              </Button>
            </a>
          </DialogHeader>

          {/* Spinner mientras se descarga el blob */}
          {loadState === 'loading' && (
            <div className="flex flex-1 items-center justify-center gap-3 text-gray-400">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Cargando documento…</span>
            </div>
          )}

          {/* PDF / imagen: renderizar en iframe con blob URL */}
          {loadState === 'preview' && blobUrl && (
            <iframe
              key={blobUrl}
              src={blobUrl}
              className="h-full w-full flex-1 rounded-b-lg border-0"
              title={anexoAbierto?.nombreArchivo}
            />
          )}

          {/* Tipo no previsualizable (DOCX, XLS, ZIP…): descargado automáticamente */}
          {loadState === 'no-preview' && (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
              <FileX size={48} className="text-gray-300" />
              <p className="text-sm text-gray-500">
                Este tipo de archivo no puede previsualizarse en el navegador.
                <br />
                El archivo se ha descargado automáticamente.
              </p>
              <a
                href={anexoAbierto?.urlArchivo}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline">
                  <Download size={14} />
                  Descargar de nuevo
                </Button>
              </a>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
