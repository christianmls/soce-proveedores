'use server'

import { prisma } from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function getProcesos() {
  try {
    const procesos = await prisma.proceso.findMany({
      include: {
        categoria: true,
      },
      orderBy: { id: 'desc' },
    })
    return procesos
  } catch (error) {
    console.error('Error loading procesos:', error)
    return []
  }
}

export async function createProceso(formData: FormData) {
  try {
    const codigoProceso = formData.get('codigoProceso') as string
    const nombre = formData.get('nombre') as string
    const categoriaId = formData.get('categoriaId') as string

    if (!codigoProceso || !categoriaId) {
      return { error: 'Código y categoría son obligatorios' }
    }

    await prisma.proceso.create({
      data: {
        codigoProceso,
        nombre: nombre || '',
        fechaCreacion: new Date(),
        categoriaId: parseInt(categoriaId),
      },
    })

    revalidatePath('/procesos')
    return { success: true }
  } catch (error) {
    console.error('Error creating proceso:', error)
    return { error: 'Error al crear el proceso' }
  }
}

export async function deleteProceso(procesoId: number) {
  try {
    // Prisma manejará la cascada automáticamente gracias al onDelete: Cascade
    await prisma.proceso.delete({
      where: { id: procesoId },
    })

    revalidatePath('/procesos')
    return { success: true }
  } catch (error) {
    console.error('Error deleting proceso:', error)
    return { error: 'Error al eliminar el proceso' }
  }
}

export async function getProcesoDetalle(procesoId: number) {
  try {
    const proceso = await prisma.proceso.findUnique({
      where: { id: procesoId },
      include: { categoria: true },
    })

    if (!proceso) {
      return null
    }

    // Usar el último barrido que tenga al menos una oferta.
    // Así, un barrido vacío (proveedores sin datos) no oculta los resultados anteriores.
    const barridoConOfertas = await prisma.barrido.findFirst({
      where: {
        procesoId,
        ofertas: { some: {} },
      },
      orderBy: { id: 'desc' },
      include: {
        ofertas: true,
        anexos: true,
      },
    })

    const ofertas = barridoConOfertas?.ofertas || []
    const anexos = barridoConOfertas?.anexos || []

    // Buscar datos de los proveedores para los RUCs con ofertas
    const rucs = [...new Set(ofertas.map((o) => o.rucProveedor))]
    const proveedores = await prisma.proveedor.findMany({
      where: { ruc: { in: rucs } },
    })
    const proveedoresByRuc = Object.fromEntries(proveedores.map((p) => [p.ruc, p]))

    return {
      proceso,
      ofertas,
      anexos,
      proveedoresByRuc,
    }
  } catch (error) {
    console.error('Error loading proceso detalle:', error)
    return null
  }
}
