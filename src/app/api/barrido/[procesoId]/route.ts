import { NextRequest } from 'next/server'
import { prisma } from '@/lib/prisma'
import { scrapeProceso } from '@/lib/scraper'
import { revalidatePath } from 'next/cache'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ procesoId: string }> },
) {
  const { procesoId: procesoIdStr } = await params
  const procesoId = parseInt(procesoIdStr, 10)

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`))
      }

      try {
        const proceso = await prisma.proceso.findUnique({ where: { id: procesoId } })
        if (!proceso) {
          send({ type: 'error', message: 'Proceso no encontrado' })
          controller.close()
          return
        }

        const proveedores = await prisma.proveedor.findMany({
          where: { categoriaId: proceso.categoriaId },
        })

        if (proveedores.length === 0) {
          send({ type: 'error', message: 'No hay proveedores en esta categoría' })
          controller.close()
          return
        }

        const barrido = await prisma.barrido.create({
          data: { procesoId, fechaInicio: new Date(), estado: 'en_proceso' },
        })

        send({ type: 'start', total: proveedores.length })

        let exitosos = 0
        let sinDatos = 0
        let errores = 0
        let nicGuardado = false
        const startTime = Date.now()

        for (let i = 0; i < proveedores.length; i++) {
          const proveedor = proveedores[i]

          // ETA based on average time for previous providers
          const elapsed = Date.now() - startTime
          const avgMs = i > 0 ? elapsed / i : null
          const remaining = avgMs !== null ? Math.round(((proveedores.length - i) * avgMs) / 1000) : null

          send({
            type: 'progress',
            current: i + 1,
            total: proveedores.length,
            ruc: proveedor.ruc,
            nombre: proveedor.nombre || proveedor.ruc,
            remaining,
          })

          try {
            const timeoutPromise = new Promise<never>((_, reject) =>
              setTimeout(() => reject(new Error('Timeout')), 60000),
            )

            const resultado = (await Promise.race([
              scrapeProceso(proceso.codigoProceso, proveedor.ruc),
              timeoutPromise,
            ])) as Awaited<ReturnType<typeof scrapeProceso>>

            if (resultado && resultado.items.length > 0) {
              // Guardar NIC en Proceso.nombre la primera vez que lo encontramos
              if (!nicGuardado && resultado.nic) {
                await prisma.proceso.update({
                  where: { id: procesoId },
                  data: { nombre: resultado.nic },
                })
                nicGuardado = true
              }

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
              send({ type: 'result', ruc: proveedor.ruc, status: 'ok' })
            } else {
              // Aún sin oferta puede traer el NIC — guardarlo si no se ha hecho aún
              if (!nicGuardado && resultado?.nic) {
                await prisma.proceso.update({
                  where: { id: procesoId },
                  data: { nombre: resultado.nic },
                })
                nicGuardado = true
              }
              sinDatos++
              send({ type: 'result', ruc: proveedor.ruc, status: 'no-data' })
            }
          } catch (error) {
            console.error(`Error procesando ${proveedor.ruc}:`, error)
            errores++
            send({ type: 'result', ruc: proveedor.ruc, status: 'error' })
          }

          await new Promise((resolve) => setTimeout(resolve, 2000))
        }

        await prisma.barrido.update({
          where: { id: barrido.id },
          data: { fechaFin: new Date(), estado: 'completado' },
        })

        revalidatePath(`/procesos/${procesoId}`)

        send({ type: 'done', exitosos, sinDatos, errores })
      } catch (error) {
        console.error('Error en barrido SSE:', error)
        send({ type: 'error', message: 'Error general en el barrido' })
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  })
}
