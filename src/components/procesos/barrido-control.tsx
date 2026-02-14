'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Play, Loader2, CheckCircle, XCircle, MinusCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

type Status = 'ok' | 'no-data' | 'error' | 'pending'

interface ProveedorLog {
  ruc: string
  nombre: string
  status: Status
}

interface BarridoControlProps {
  procesoId: number
  categoriaId: number
}

function formatRemaining(secs: number): string {
  if (secs < 60) return `${secs}s`
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return s > 0 ? `${m}m ${s}s` : `${m}m`
}

export function BarridoControl({ procesoId }: BarridoControlProps) {
  const router = useRouter()
  const [isRunning, setIsRunning] = useState(false)
  const [total, setTotal] = useState(0)
  const [current, setCurrent] = useState(0)
  const [currentRuc, setCurrentRuc] = useState('')
  const [currentNombre, setCurrentNombre] = useState('')
  const [remaining, setRemaining] = useState<number | null>(null)
  const [logs, setLogs] = useState<ProveedorLog[]>([])
  const [done, setDone] = useState<{ exitosos: number; sinDatos: number; errores: number } | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  function handleIniciar() {
    setIsRunning(true)
    setTotal(0)
    setCurrent(0)
    setCurrentRuc('')
    setCurrentNombre('')
    setRemaining(null)
    setLogs([])
    setDone(null)
    setErrorMsg(null)

    const es = new EventSource(`/api/barrido/${procesoId}`)

    es.onmessage = (e) => {
      const data = JSON.parse(e.data as string)

      if (data.type === 'start') {
        setTotal(data.total)
      } else if (data.type === 'progress') {
        setCurrent(data.current)
        setCurrentRuc(data.ruc)
        setCurrentNombre(data.nombre)
        setRemaining(data.remaining ?? null)
        setLogs((prev) => [
          ...prev,
          { ruc: data.ruc, nombre: data.nombre, status: 'pending' },
        ])
      } else if (data.type === 'result') {
        setLogs((prev) => {
          const updated = [...prev]
          for (let i = updated.length - 1; i >= 0; i--) {
            if (updated[i].ruc === data.ruc && updated[i].status === 'pending') {
              updated[i] = { ...updated[i], status: data.status }
              break
            }
          }
          return updated
        })
      } else if (data.type === 'done') {
        setDone({ exitosos: data.exitosos, sinDatos: data.sinDatos, errores: data.errores })
        setIsRunning(false)
        setCurrentRuc('')
        es.close()
        router.refresh()
      } else if (data.type === 'error') {
        setErrorMsg(data.message)
        setIsRunning(false)
        es.close()
      }
    }

    es.onerror = () => {
      setErrorMsg('Error de conexión con el servidor')
      setIsRunning(false)
      es.close()
    }
  }

  const pct = total > 0 ? Math.round((current / total) * 100) : 0
  const showProgress = isRunning || (logs.length > 0 && !done)

  return (
    <div className="space-y-3">
      {/* Botón + resumen final */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Button
            onClick={handleIniciar}
            disabled={isRunning}
            className="bg-green-600 hover:bg-green-700"
            size="lg"
          >
            {isRunning ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                <Play size={16} />
                Iniciar Barrido
              </>
            )}
          </Button>

          {done && (
            <p className="text-sm font-medium text-green-700">
              Completado — {done.exitosos} con oferta · {done.sinDatos} sin datos
              {done.errores > 0 && (
                <span className="text-red-600"> · {done.errores} errores</span>
              )}
            </p>
          )}
          {errorMsg && <p className="text-sm font-medium text-red-600">{errorMsg}</p>}
        </div>
      </Card>

      {/* Barra de progreso */}
      {showProgress && (
        <Card>
          <CardContent className="space-y-3 pt-4">
            <div>
              <div className="mb-1 flex justify-between text-xs text-gray-500">
                <span>
                  {current} / {total} proveedores
                </span>
                <span>
                  {pct}%
                  {remaining !== null && ` · ETA ${formatRemaining(remaining)}`}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-green-500 transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>

            {currentRuc && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Procesando:</span>{' '}
                {currentNombre !== currentRuc ? (
                  <>
                    {currentNombre}{' '}
                    <span className="font-mono text-xs text-gray-400">{currentRuc}</span>
                  </>
                ) : (
                  <span className="font-mono text-xs">{currentRuc}</span>
                )}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Registro de proveedores */}
      {logs.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <p className="mb-2 text-sm font-bold text-gray-700">Registro de proveedores</p>
            <div className="max-h-52 space-y-1 overflow-y-auto pr-1">
              {[...logs].reverse().map((log, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {log.status === 'pending' && (
                    <Loader2 size={14} className="shrink-0 animate-spin text-gray-400" />
                  )}
                  {log.status === 'ok' && (
                    <CheckCircle size={14} className="shrink-0 text-green-500" />
                  )}
                  {log.status === 'no-data' && (
                    <MinusCircle size={14} className="shrink-0 text-gray-400" />
                  )}
                  {log.status === 'error' && (
                    <XCircle size={14} className="shrink-0 text-red-500" />
                  )}
                  <span className="shrink-0 font-mono text-xs text-gray-400">{log.ruc}</span>
                  <span className="truncate text-gray-700">{log.nombre}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
