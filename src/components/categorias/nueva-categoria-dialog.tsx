'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { createCategoria } from '@/app/actions/categorias'

export function NuevaCategoriaDialog() {
  const [open, setOpen] = useState(false)

  async function handleSubmit(formData: FormData) {
    const result = await createCategoria(formData)
    if (result.success) {
      setOpen(false)
    } else {
      alert(result.error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-green-600 hover:bg-green-700">
          <Plus size={18} />
          Nueva Categoría
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Añadir Categoría</DialogTitle>
        </DialogHeader>
        <form action={handleSubmit} className="space-y-4">
          <div>
            <Input name="nombre" placeholder="Nombre" required />
          </div>
          <div>
            <Textarea
              name="descripcion"
              placeholder="Descripción (opcional)"
              rows={3}
            />
          </div>
          <Button type="submit" className="w-full bg-green-600 hover:bg-green-700">
            Guardar
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
