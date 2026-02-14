'use server'

import { prisma } from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function getCategorias() {
  try {
    const categorias = await prisma.categoria.findMany({
      orderBy: { id: 'desc' },
    })
    return categorias
  } catch (error) {
    console.error('Error loading categorias:', error)
    return []
  }
}

export async function createCategoria(formData: FormData) {
  try {
    const nombre = formData.get('nombre') as string
    const descripcion = formData.get('descripcion') as string

    if (!nombre) {
      return { error: 'El nombre es obligatorio' }
    }

    await prisma.categoria.create({
      data: {
        nombre,
        descripcion: descripcion || '',
      },
    })

    revalidatePath('/categorias')
    return { success: true }
  } catch (error) {
    console.error('Error creating categoria:', error)
    return { error: 'Error al crear la categoría' }
  }
}
