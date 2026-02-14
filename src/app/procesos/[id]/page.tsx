import Link from 'next/link'
import { ArrowLeft, Inbox } from 'lucide-react'
import { getProcesoDetalle } from '@/app/actions/procesos'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarridoControl } from '@/components/procesos/barrido-control'
import { OfertasTabla } from '@/components/procesos/ofertas-tabla'

export default async function ProcesoDetallePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const procesoId = parseInt(id)
  const data = await getProcesoDetalle(procesoId)

  if (!data) {
    return <div className="p-8">Proceso no encontrado</div>
  }

  const { proceso, ofertas, anexos, proveedoresByRuc } = data

  // Agrupar ofertas por RUC
  const ofertasPorRuc = ofertas.reduce((acc, oferta) => {
    if (!acc[oferta.rucProveedor]) {
      acc[oferta.rucProveedor] = []
    }
    acc[oferta.rucProveedor].push(oferta)
    return acc
  }, {} as Record<string, typeof ofertas>)

  const rucs = Object.keys(ofertasPorRuc)

  return (
    <div className="p-8">
      <div className="mb-4 flex items-center justify-between">
        <Link href="/procesos">
          <Button variant="ghost">
            <ArrowLeft size={16} />
            Volver
          </Button>
        </Link>
      </div>

      <BarridoControl procesoId={procesoId} categoriaId={proceso.categoriaId} />

      {rucs.length === 0 ? (
        <Card className="mt-6">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Inbox size={48} className="mb-4 text-gray-400" />
            <h3 className="mb-2 text-xl font-bold">No hay ofertas disponibles</h3>
            <p className="text-gray-500">Inicia un barrido para ver resultados</p>
          </CardContent>
        </Card>
      ) : (
        <div className="mt-6 space-y-6">
          {rucs.map((ruc) => (
            <OfertasTabla
              key={ruc}
              ruc={ruc}
              ofertas={ofertasPorRuc[ruc]}
              anexos={anexos.filter((a) => a.rucProveedor === ruc)}
              proveedor={proveedoresByRuc[ruc] ?? null}
            />
          ))}
        </div>
      )}
    </div>
  )
}
