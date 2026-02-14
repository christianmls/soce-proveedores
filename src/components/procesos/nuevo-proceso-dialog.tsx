'use client'

import { useState, useEffect } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { createProceso } from '@/app/actions/procesos'
import { getCategorias } from '@/app/actions/categorias'

export function NuevoProcesoDialog() {
  const [open, setOpen] = useState(false)
  const [categorias, setCategorias] = useState<any[]>([])
  const [selectedCategoria, setSelectedCategoria] = useState('')

  useEffect(() => {
    getCategorias().then(setCategorias)
  }, [])

  async function handleSubmit(formData: FormData) {
    formData.append('categoriaId', selectedCategoria)
    const result = await createProceso(formData)
    if (result.success) {
      setOpen(false)
      setSelectedCategoria('')
    } else {
      alert(result.error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-green-600 hover:bg-green-700" size="lg">
          <Plus size={18} />
          Nuevo Proceso
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Crear Nuevo Proceso</DialogTitle>
          <DialogDescription>
            Ingresa los datos del proceso de contratación
          </DialogDescription>
        </DialogHeader>
        <form action={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-bold">Código del Proceso</label>
            <Input
              name="codigoProceso"
              placeholder="ej: PEK4fvqKamCKkU3DU_Ota3z..."
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold">Nombre (opcional)</label>
            <Input name="nombre" placeholder="Nombre descriptivo del proceso" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-bold">Categoría</label>
            <Select value={selectedCategoria} onValueChange={setSelectedCategoria}>
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar Categoría..." />
              </SelectTrigger>
              <SelectContent>
                {categorias.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" className="bg-green-600 hover:bg-green-700">
              Guardar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
