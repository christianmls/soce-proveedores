import { getProveedores } from '@/app/actions/proveedores'
import { NuevoProveedorDialog } from '@/components/proveedores/nuevo-proveedor-dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export default async function ProveedoresPage() {
  const proveedores = await getProveedores()

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Base de Proveedores</h1>
        <NuevoProveedorDialog />
      </div>

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>RUC</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Contacto</TableHead>
              <TableHead>Categoría</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {proveedores.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-gray-500">
                  No hay proveedores registrados
                </TableCell>
              </TableRow>
            ) : (
              proveedores.map((proveedor) => (
                <TableRow key={proveedor.id}>
                  <TableCell className="font-mono">{proveedor.ruc}</TableCell>
                  <TableCell>{proveedor.nombre}</TableCell>
                  <TableCell>{proveedor.contacto}</TableCell>
                  <TableCell>
                    {proveedor.categoria?.nombre || 'Sin categoría'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
