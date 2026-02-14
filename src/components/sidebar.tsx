'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Search, Grid2X2, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

const menuItems = [
  { name: 'Procesos', icon: Search, href: '/procesos' },
  { name: 'Categorías', icon: Grid2X2, href: '/categorias' },
  { name: 'Proveedores', icon: Users, href: '/proveedores' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 border-r border-gray-200 bg-gray-100 p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-green-600">SOCE Pro</h1>
        <p className="text-xs text-gray-600">Sistema de Ofertas</p>
      </div>

      <nav className="space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-green-100 text-green-700'
                  : 'text-gray-700 hover:bg-gray-200'
              )}
            >
              <Icon size={18} />
              {item.name}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
