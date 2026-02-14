import Link from 'next/link'
import { Eye, Inbox } from 'lucide-react'
import { getProcesos } from '@/app/actions/procesos'
import { NuevoProcesoDialog } from '@/components/procesos/nuevo-proceso-dialog'
import { EliminarProcesoButton } from '@/components/procesos/eliminar-proceso-button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export default async function ProcesosPage() {
  const procesos = await getProcesos()

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Procesos de Contratación</h1>
        <NuevoProcesoDialog />
      </div>

      {procesos.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Inbox size={48} className="mb-4 text-gray-400" />
            <h3 className="mb-2 text-xl font-bold">No hay procesos registrados</h3>
            <p className="text-gray-500">Crea un nuevo proceso para comenzar</p>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>NIC</TableHead>
                <TableHead>Código</TableHead>
                <TableHead>Fecha Creación</TableHead>
                <TableHead className="w-[150px]">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {procesos.map((proceso) => (
                <TableRow key={proceso.id}>
                  <TableCell className="font-mono font-semibold text-green-700">
                    {proceso.nombre || <span className="text-gray-400">—</span>}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-gray-500">{proceso.codigoProceso}</TableCell>
                  <TableCell className="text-gray-600">
                    {proceso.fechaCreacion
                      ? new Date(proceso.fechaCreacion).toLocaleString('es-EC')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Link href={`/procesos/${proceso.id}`}>
                        <Button variant="outline" size="sm">
                          <Eye size={16} />
                        </Button>
                      </Link>
                      <EliminarProcesoButton procesoId={proceso.id} />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
