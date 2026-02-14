'use client'

import { useState, useEffect } from 'react'
import { UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
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
import { createProveedor } from '@/app/actions/proveedores'
import { getCategorias } from '@/app/actions/categorias'

export function NuevoProveedorDialog() {
  const [open, setOpen] = useState(false)
  const [categorias, setCategorias] = useState<any[]>([])
  const [selectedCategoria, setSelectedCategoria] = useState('')

  useEffect(() => {
    getCategorias().then(setCategorias)
  }, [])

  async function handleSubmit(formData: FormData) {
    formData.append('categoriaId', selectedCategoria)
    const result = await createProveedor(formData)
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
        <Button className="bg-green-600 hover:bg-green-700">
          <UserPlus size={18} />
          Agregar Proveedor
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nuevo Proveedor</DialogTitle>
        </DialogHeader>
        <form action={handleSubmit} className="space-y-4">
          <div>
            <Input name="ruc" placeholder="RUC (Obligatorio)" required />
          </div>
          <div>
            <Input name="nombre" placeholder="Nombre (Opcional)" />
          </div>
          <div>
            <Input name="contacto" placeholder="Contacto (Opcional)" />
          </div>
          <div>
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
          <Button type="submit" className="w-full bg-green-600 hover:bg-green-700">
            Guardar
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
