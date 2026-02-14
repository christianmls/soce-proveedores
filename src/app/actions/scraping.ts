'use server'

import { prisma } from '@/lib/prisma'
import { scrapeProceso } from '@/lib/scraper'
import { revalidatePath } from 'next/cache'

export async function iniciarBarrido(procesoId: number) {
  try {
    // Obtener proceso y proveedores
    const proceso = await prisma.proceso.findUnique({
      where: { id: procesoId },
    })

    if (!proceso) {
      return { error: 'Proceso no encontrado' }
    }

    const proveedores = await prisma.proveedor.findMany({
      where: { categoriaId: proceso.categoriaId },
    })

    if (proveedores.length === 0) {
      return { error: 'No hay proveedores en esta categoría' }
    }

    // Crear barrido
    const barrido = await prisma.barrido.create({
      data: {
        procesoId,
        fechaInicio: new Date(),
        estado: 'en_proceso',
      },
    })

    let exitosos = 0
    let sinDatos = 0
    let errores = 0

    // Procesar cada proveedor
    for (const proveedor of proveedores) {
      try {
        // Timeout de 60 segundos por proveedor
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), 60000)
        )

        const resultado = await Promise.race([
          scrapeProceso(proceso.codigoProceso, proveedor.ruc),
          timeoutPromise,
        ]) as Awaited<ReturnType<typeof scrapeProceso>>

        if (resultado && resultado.items.length > 0 && resultado.total > 0) {
          // Actualizar datos del proveedor
          if (resultado.proveedor.razonSocial) {
            await prisma.proveedor.update({
              where: { id: proveedor.id },
              data: {
                nombre: resultado.proveedor.razonSocial,
                correo: resultado.proveedor.correo,
                telefono: resultado.proveedor.telefono,
                pais: resultado.proveedor.pais,
                provincia: resultado.proveedor.provincia,
                canton: resultado.proveedor.canton,
                direccion: resultado.proveedor.direccion,
              },
            })
          }

          // Guardar ofertas
          for (const item of resultado.items) {
            await prisma.oferta.create({
              data: {
                barridoId: barrido.id,
                rucProveedor: proveedor.ruc,
                razonSocial: resultado.proveedor.razonSocial || proveedor.nombre,
                numeroItem: item.numero,
                cpc: item.cpc,
                descripcionProducto: item.desc,
                unidad: item.unid,
                cantidad: item.cant,
                valorUnitario: item.v_unit,
                valorTotal: item.v_tot,
                fechaScraping: new Date(),
              },
            })
          }

          // Guardar anexos
          for (const anexo of resultado.anexos) {
            await prisma.anexo.create({
              data: {
                barridoId: barrido.id,
                rucProveedor: proveedor.ruc,
                nombreArchivo: anexo.nombre,
                urlArchivo: anexo.url,
                fechaRegistro: new Date(),
              },
            })
          }

          exitosos++
        } else {
          sinDatos++
        }

        // Pausa entre requests
        await new Promise((resolve) => setTimeout(resolve, 2000))
      } catch (error) {
        console.error(`Error procesando ${proveedor.ruc}:`, error)
        errores++
      }
    }

    // Finalizar barrido
    await prisma.barrido.update({
      where: { id: barrido.id },
      data: {
        fechaFin: new Date(),
        estado: 'completado',
      },
    })

    revalidatePath(`/procesos/${procesoId}`)

    return {
      success: true,
      mensaje: `Completado: ${exitosos} exitosos, ${sinDatos} sin datos, ${errores} errores`,
    }
  } catch (error) {
    console.error('Error en barrido:', error)
    return { error: 'Error general en el barrido' }
  }
}
