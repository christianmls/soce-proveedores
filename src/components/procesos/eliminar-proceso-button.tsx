'use client'

import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { deleteProceso } from '@/app/actions/procesos'

export function EliminarProcesoButton({ procesoId }: { procesoId: number }) {
  async function handleDelete() {
    if (!confirm('¿Estás seguro de eliminar este proceso y todos sus datos?')) {
      return
    }

    const result = await deleteProceso(procesoId)
    if (result.error) {
      alert(result.error)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={handleDelete} className="text-red-600">
      <Trash2 size={16} />
    </Button>
  )
}
