'use server'

import { prisma } from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function getProveedores() {
  try {
    const proveedores = await prisma.proveedor.findMany({
      include: {
        categoria: true,
      },
      orderBy: { id: 'desc' },
    })
    return proveedores
  } catch (error) {
    console.error('Error loading proveedores:', error)
    return []
  }
}

export async function createProveedor(formData: FormData) {
  try {
    const ruc = formData.get('ruc') as string
    const nombre = formData.get('nombre') as string
    const contacto = formData.get('contacto') as string
    const categoriaId = formData.get('categoriaId') as string

    if (!ruc) {
      return { error: 'El RUC es obligatorio' }
    }

    await prisma.proveedor.create({
      data: {
        ruc,
        nombre: nombre || '',
        contacto: contacto || '',
        categoriaId: categoriaId ? parseInt(categoriaId) : null,
      },
    })

    revalidatePath('/proveedores')
    return { success: true }
  } catch (error) {
    console.error('Error creating proveedor:', error)
    return { error: 'Error al crear el proveedor' }
  }
}
