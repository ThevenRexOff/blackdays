'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import {
  LayoutDashboard,
  Zap,
  ChevronDown,
  ChevronRight,
  Shield,
  CreditCard,
  Hash,
  Sparkles,
  ShoppingCart,
  User,
  ShieldCheck,
  Mail
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Gate {
  id: string
  name: string
  category: 'auth' | 'charged' | 'ccn' | 'special' | 'shopify'
}

const categoryIcons = {
  auth: Shield,
  charged: CreditCard,
  ccn: Hash,
  special: Sparkles,
  shopify: ShoppingCart,
}

const categoryLabels = {
  auth: 'Auth Gates',
  charged: 'Charged Gates',
  ccn: 'CCN Gates',
  special: 'Special Gates',
  shopify: 'Shopify Gates',
}

const categoryOrder = ['auth', 'charged', 'ccn', 'special', 'shopify'] as const

export function Sidebar() {
  const pathname = usePathname()
  const { data: session } = useSession()
  const [gatesOpen, setGatesOpen] = useState(true)
  const [gates, setGates] = useState<Gate[]>([])
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({})
  const rank = session?.user?.rank
  const isAdmin = rank === 'admin'
  const isManager = rank === 'admin' || rank === 'moderador' || rank === 'seller'

  useEffect(() => {
    const fetchGates = async () => {
      try {
        const res = await fetch('/api/gates')
        const data = await res.json()
        const activeGates = data
          .filter((g: Gate & { isActive: boolean }) => g.isActive)
          .map((g: Gate) => ({ id: g.id, name: g.name, category: g.category }))
        setGates(activeGates)
      } catch {}
    }
    fetchGates()
    const handler = () => fetchGates()
    window.addEventListener('gates-updated', handler)
    return () => window.removeEventListener('gates-updated', handler)
  }, [])

  const gatesByCategory = gates.reduce((acc, gate) => {
    if (!acc[gate.category]) {
      acc[gate.category] = []
    }
    acc[gate.category].push(gate)
    return acc
  }, {} as Record<string, Gate[]>)

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  return (
    <aside className="flex w-64 flex-col border-r border-purple-900/30 bg-[#050505] relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-20">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="sidebar-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(147, 51, 234, 0.15)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#sidebar-grid)" />
        </svg>
      </div>

      {/* Corner geometric decorations */}
      <div className="absolute left-0 top-0 w-32 h-32 pointer-events-none z-10">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <path d="M0,0 L40,0 L40,2 L2,2 L2,40 L0,40 Z" fill="rgba(147, 51, 234, 0.4)" />
          <path d="M0,10 L30,10 L30,12 L2,12 L2,30 L0,30 Z" fill="rgba(147, 51, 234, 0.25)" />
          <path d="M10,0 L10,20 L12,20 L12,0 Z" fill="rgba(147, 51, 234, 0.2)" />
          <circle cx="25" cy="25" r="2" fill="rgba(147, 51, 234, 0.5)" />
        </svg>
      </div>

      {/* Logo Section */}
      <div className="relative flex flex-col items-center border-b border-purple-900/30 py-6 z-10">
        <div className="relative">
          <div className="relative h-20 w-20 rounded-full border-2 border-purple-600/50 overflow-hidden">
            <Image
              src="/images/logo.jpg"
              alt="JILL CHK Logo"
              fill
              className="object-cover"
            />
            <div className="absolute inset-0 bg-purple-600/10 animate-pulse" />
          </div>
        </div>
        
        <h1 className="mt-3 font-mono text-sm font-bold tracking-[0.2em] text-white">
          JILL CHK
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 z-10 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-purple-900/50">
        <ul className="space-y-1">
          {/* Dashboard Link */}
          <li>
            <Link
              href="/dashboard"
              className={cn(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 font-mono text-xs font-medium tracking-wider transition-all duration-200',
                pathname === '/dashboard'
                  ? 'bg-gradient-to-r from-purple-600/20 to-transparent text-purple-400 border-l-2 border-purple-500' 
                  : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 border-l-2 border-transparent'
              )}
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
              {pathname === '/dashboard' && (
                <div className="absolute right-2 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
              )}
            </Link>
          </li>

          {/* Gates Section with Submenu */}
          <li>
            <button
              onClick={() => setGatesOpen(!gatesOpen)}
              className={cn(
                'group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 font-mono text-xs font-medium tracking-wider transition-all duration-200',
                pathname.includes('/gates')
                  ? 'bg-gradient-to-r from-purple-600/20 to-transparent text-purple-400 border-l-2 border-purple-500' 
                  : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 border-l-2 border-transparent'
              )}
            >
              <Zap className="h-4 w-4" />
              Gates
              <ChevronDown className={cn(
                "ml-auto h-4 w-4 transition-transform duration-200",
                gatesOpen ? "rotate-0" : "-rotate-90"
              )} />
            </button>

            {gatesOpen && (
              <div className="mt-1 ml-2 pl-4 border-l border-purple-900/30 space-y-1">
                {/* Ver Todos Link */}
                <Link
                  href="/dashboard/gates"
                  className={cn(
                    'flex items-center gap-2 rounded-md px-3 py-2 text-xs transition-all duration-200',
                    pathname === '/dashboard/gates'
                      ? 'bg-purple-600/20 text-purple-400'
                      : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300'
                  )}
                >
                  <Zap className="h-3 w-3" />
                  Ver Todos
                </Link>

                {/* Categories with Gates */}
                {categoryOrder.map((category) => {
                  const CategoryIcon = categoryIcons[category]
                  const categoryGates = gatesByCategory[category] || []
                  
                  return (
                    <div key={category}>
            <button
              onClick={() => toggleCategory(category)}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 transition-all duration-200 cursor-pointer"
            >
              <CategoryIcon className="h-3 w-3" />
              <span className="flex-1 text-left">{categoryLabels[category]}</span>
                        {categoryGates.length > 0 && (
                          <>
                            <span className="text-purple-500/70 text-[10px]">({categoryGates.length})</span>
                            <ChevronRight className={cn(
                              "h-3 w-3 transition-transform duration-200",
                              expandedCategories[category] ? "rotate-90" : ""
                            )} />
                          </>
                        )}
                      </button>
                      
                      {expandedCategories[category] && categoryGates.length > 0 && (
                        <div className="ml-4 space-y-0.5">
                          {categoryGates.map((gate) => (
                            <Link
                              key={gate.id}
                              href={`/dashboard/gates/${gate.id}`}
                              className={cn(
                                'flex items-center gap-2 rounded-md px-3 py-1.5 text-[11px] transition-all duration-200',
                                pathname === `/dashboard/gates/${gate.id}`
                                  ? 'bg-purple-600/20 text-purple-400'
                                  : 'text-gray-600 hover:bg-purple-900/10 hover:text-gray-400'
                              )}
                            >
                              <div className="h-1.5 w-1.5 rounded-full bg-purple-500/50" />
                              {gate.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </li>

          {/* Perfil Link */}
          <li>
            <Link
              href="/dashboard/perfil"
              className={cn(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 font-mono text-xs font-medium tracking-wider transition-all duration-200',
                pathname === '/dashboard/perfil'
                  ? 'bg-gradient-to-r from-purple-600/20 to-transparent text-purple-400 border-l-2 border-purple-500'
                  : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 border-l-2 border-transparent'
              )}
            >
              <User className="h-4 w-4" />
              Perfil
              {pathname === '/dashboard/perfil' && (
                <div className="absolute right-2 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
              )}
            </Link>
          </li>

          {/* TempMail Link */}
          <li>
            <Link
              href="/dashboard/tempmail"
              className={cn(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 font-mono text-xs font-medium tracking-wider transition-all duration-200',
                pathname === '/dashboard/tempmail'
                  ? 'bg-gradient-to-r from-purple-600/20 to-transparent text-purple-400 border-l-2 border-purple-500'
                  : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 border-l-2 border-transparent'
              )}
            >
              <Mail className="h-4 w-4" />
              Temp Mail
              {pathname === '/dashboard/tempmail' && (
                <div className="absolute right-2 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
              )}
            </Link>
          </li>

          {/* Admin Section */}
          {isManager && (
            <li>
              <Link
                href="/dashboard/admin"
                className={cn(
                  'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 font-mono text-xs font-medium tracking-wider transition-all duration-200',
                  pathname.startsWith('/dashboard/admin')
                    ? 'bg-gradient-to-r from-purple-600/20 to-transparent text-purple-400 border-l-2 border-purple-500'
                    : 'text-gray-500 hover:bg-purple-900/10 hover:text-gray-300 border-l-2 border-transparent'
                )}
              >
                <ShieldCheck className="h-4 w-4" />
                Administración
                {pathname.startsWith('/dashboard/admin') && (
                  <div className="absolute right-2 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
                )}
              </Link>
            </li>
          )}

        </ul>
      </nav>

      {/* Bottom decoration */}
      <div className="relative h-36 overflow-hidden border-t border-purple-900/30 z-10">
        <div className="absolute inset-0 bg-gradient-to-t from-purple-600/20 via-purple-900/10 to-transparent" />
        <Image
          src="/images/pirate-ship-silhouette.jpg"
          alt="Pirate Ship"
          fill
          className="object-cover opacity-50"
        />
        <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(147,51,234,0.02)_50%)] bg-[length:100%_4px]" />
      </div>
    </aside>
  )
}
