'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Zap, ShieldCheck, CreditCard, Sparkles, Lock, ArrowRight, Terminal, ShoppingCart } from 'lucide-react'

interface GateStats {
  lives: number
  deads: number
  successRate: number
  total: number
}

interface Gate {
  id: string
  name: string
  category: 'auth' | 'charged' | 'ccn' | 'special' | 'shopify'
  description: string
  isActive: boolean
  creditsLive: number
  creditsDead: number
  minRank: string
  threads: number
  stats: GateStats
  createdAt: string
}

const categoryConfig = {
  auth: {
    icon: ShieldCheck,
    color: 'from-red-600 to-red-900',
    border: 'border-red-500/50',
    text: 'text-red-400',
    bg: 'bg-red-500/10',
    hoverBorder: 'neon-border-red'
  },
  charged: {
    icon: CreditCard,
    color: 'from-orange-600 to-orange-900',
    border: 'border-orange-500/50',
    text: 'text-orange-400',
    bg: 'bg-orange-500/10',
    hoverBorder: 'neon-border-red'
  },
  ccn: {
    icon: Lock,
    color: 'from-yellow-600 to-yellow-900',
    border: 'border-yellow-500/50',
    text: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    hoverBorder: 'neon-border-orange'
  },
  special: {
    icon: Sparkles,
    color: 'from-rose-600 to-rose-900',
    border: 'border-rose-500/50',
    text: 'text-rose-400',
    bg: 'bg-rose-500/10',
    hoverBorder: 'neon-border-red'
  },
  shopify: {
    icon: ShoppingCart,
    color: 'from-orange-600 to-red-900',
    border: 'border-orange-500/50',
    text: 'text-orange-400',
    bg: 'bg-orange-500/10',
    hoverBorder: 'neon-border-orange'
  }
}

export default function GatesListPage() {
  const [gates, setGates] = useState<Gate[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    async function fetchGates() {
      try {
        const res = await fetch('/api/gates')
        const data = await res.json()
        setGates(data)
      } catch (error) {
        console.error('Error fetching gates:', error)
      }
      setLoading(false)
    }

    fetchGates()
  }, [])

  const filteredGates = filter === 'all'
    ? gates
    : gates.filter(gate => gate.category === filter)

  if (loading) {
    return <div className="matrix-bg rounded-xl min-h-[500px]" />
  }

  return (
    <div className="space-y-8 p-6 matrix-bg min-h-screen rounded-xl border border-red-900/30">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-red-500/20 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Zap className="h-10 w-10 text-red-500 animate-pulse-glow" />
            <h1 className="text-4xl font-black uppercase tracking-widest text-white neon-text-red">
              GATES
            </h1>
          </div>
          <p className="mt-2 font-mono-cyber text-sm text-red-500/80 uppercase">
            &gt; Selecciona un gate para comenzar a verificar
          </p>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setFilter('all')}
          className={`cyber-clip-alt px-6 py-2.5 font-mono-cyber text-sm font-bold uppercase transition-all duration-300 cursor-pointer ${filter === 'all'
            ? 'bg-red-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.6)]'
            : 'border border-red-500/30 bg-black/60 text-red-500 hover:bg-red-900/30'
            }`}
        >
          [ Todos los Gates ]
        </button>
        {Object.entries(categoryConfig).map(([key, config]) => {
          const Icon = config.icon
          const isActive = filter === key
          return (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`cyber-clip-alt flex items-center gap-2 px-6 py-2.5 font-mono-cyber text-sm font-bold uppercase transition-all duration-300 cursor-pointer ${isActive
                ? `bg-gradient-to-r ${config.color} text-white shadow-[0_0_15px_currentColor] border border-white/20`
                : `border ${config.border} bg-black/60 ${config.text} hover:bg-gray-900`
                }`}
            >
              <Icon className="h-4 w-4" />
              {key}
            </button>
          )
        })}
      </div>

      {/* Gates Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredGates.map((gate) => {
          const config = categoryConfig[gate.category]
          const Icon = config.icon

          return (
            <Link
              key={gate.id}
              href={`/dashboard/gates/${gate.id}`}
              className={`cyber-clip group relative overflow-hidden border ${config.border} bg-black/80 p-6 backdrop-blur-md transition-all duration-300 hover:${config.hoverBorder} glitch-hover`}
            >
              {/* Background scanline */}
              <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.25)_50%)] bg-[length:100%_4px] opacity-30 group-hover:opacity-100" />

              {/* Status indicator */}
              <div className="absolute right-4 top-4 flex items-center gap-2 border border-green-500/30 bg-green-950/40 px-2 py-1 rounded-sm">
                {gate.isActive ? (
                  <>
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]" />
                    <span className="font-mono-cyber text-[10px] text-green-400">ONLINE</span>
                  </>
                ) : (
                  <>
                    <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
                    <span className="font-mono-cyber text-[10px] text-red-500">OFFLINE</span>
                  </>
                )}
              </div>

              {/* Content */}
              <div className="relative z-10">
                <div className={`mb-4 inline-flex rounded-none border ${config.border} ${config.bg} p-3`}>
                  <Icon className={`h-6 w-6 ${config.text}`} />
                </div>

                <h3 className={`mb-1 text-xl font-black uppercase tracking-wider text-white group-hover:neon-text-red`}>
                  {gate.name}
                </h3>
                <p className="mb-4 font-mono-cyber text-xs text-gray-400 line-clamp-2 h-8">
                  {gate.description}
                </p>

                {/* Min Rank Badge */}
                <div className="mb-3 flex items-center gap-2">
                  <span className="font-mono-cyber text-[9px] uppercase tracking-widest text-gray-500">RANGO MIN:</span>
                  <span className={`uppercase font-bold text-[10px] px-2 py-0.5 border ${gate.minRank === 'admin' ? 'text-red-400 border-red-500/30 bg-red-950/30' :
                    gate.minRank === 'moderador' ? 'text-purple-400 border-purple-500/30 bg-purple-950/30' :
                      gate.minRank === 'seller' ? 'text-blue-400 border-blue-500/30 bg-blue-950/30' :
                        gate.minRank === 'vip' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-950/30' :
                          'text-green-400 border-green-500/30 bg-green-950/30'
                    }`}>{gate.minRank}</span>
                </div>

                {/* Stats Row */}
                <div className="mb-4">
                  <p className="mb-1 font-mono-cyber text-[9px] font-bold uppercase tracking-widest text-gray-500">GLOBAL STATS</p>
                  <div className="grid grid-cols-3 gap-2 font-mono-cyber text-[10px]">
                    <div className="border border-green-500/30 bg-green-950/40 px-2 py-1.5 text-center rounded">
                      <span className="text-green-400 font-bold">{gate.stats.lives}</span>
                      <span className="text-green-500 ml-1">LIVE</span>
                    </div>
                    <div className="border border-red-500/30 bg-red-950/40 px-2 py-1.5 text-center rounded">
                      <span className="text-red-400 font-bold">{gate.stats.deads}</span>
                      <span className="text-red-500 ml-1">DEAD</span>
                    </div>
                    <div className={`border px-2 py-1.5 text-center rounded ${gate.stats.successRate >= 50
                      ? 'border-green-500/30 bg-green-950/40 text-green-400'
                      : gate.stats.successRate > 0
                        ? 'border-yellow-500/30 bg-yellow-950/40 text-yellow-400'
                        : 'border-gray-600 bg-gray-800/60 text-gray-400'
                      }`}>
                      <span className="font-bold">{gate.stats.successRate}%</span>
                      <span className="ml-1 opacity-70">Rate</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-gray-800 pt-4">
                  <span className={`px-2 py-1 font-mono-cyber text-[10px] font-bold uppercase border ${config.border} ${config.bg} ${config.text}`}>
                    &lt;{gate.category}&gt;
                  </span>
                  <div className="flex items-center gap-2 font-mono-cyber text-xs">
                    <span className="flex items-center gap-1 text-green-400">
                      <Zap className="h-3 w-3" />
                      {gate.creditsLive} Live
                    </span>
                    <span className="text-gray-600">/</span>
                    <span className="flex items-center gap-1 text-red-500">
                      <Zap className="h-3 w-3" />
                      {gate.creditsDead} Dead
                    </span>
                  </div>
                </div>
              </div>

              {/* Hover UI overlay */}
              <div className="absolute bottom-4 right-4 opacity-0 transition-all duration-300 group-hover:opacity-100 group-hover:-translate-x-1">
                <ArrowRight className="h-6 w-6 text-red-500" />
              </div>

              {/* Cyberpunk corner accents */}
              <div className="absolute left-0 top-0 h-4 w-4 border-l-2 border-t-2 border-red-500/50" />
              <div className="absolute bottom-0 right-0 h-4 w-4 border-b-2 border-r-2 border-red-500/50" />
            </Link>
          )
        })}
      </div>

      {/* Empty state */}
      {filteredGates.length === 0 && (
        <div className="flex flex-col items-center justify-center border border-dashed border-red-500/30 bg-red-950/10 py-20 cyber-clip">
          <Terminal className="h-16 w-16 text-red-500/50 mb-4" />
          <h3 className="font-mono-cyber text-lg font-bold text-red-500 uppercase tracking-widest neon-text-red">ERROR: GATE NO ENCONTRADO</h3>
          <p className="mt-2 font-mono-cyber text-sm text-red-400/70">
            {filter === 'all'
              ? '> No hay gates activos.'
              : `> El filtro '${filter}' no obtuvo resultados.`}
          </p>
        </div>
      )}
    </div>
  )
}

