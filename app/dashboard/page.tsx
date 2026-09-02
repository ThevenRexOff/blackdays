'use client'

import { useEffect, useState, useRef } from 'react'
import { useSession } from 'next-auth/react'
import { Zap, Shield, Users, Activity, CheckCircle2, XCircle, Terminal, Globe, CreditCard, Hash, Sparkles, ShoppingCart, BarChart3, UserPlus, Plus, TrendingUp } from 'lucide-react'
import { useCounter } from '@/hooks/use-counter'
import { DashboardParticles } from '@/components/dashboard/dashboard-particles'

interface DashboardData {
  userCount: number
  recentUsers: { username: string; createdAt: string }[]
  topUsers: { username: string; lives: number; deads: number; rank: string }[]
  gateCount: number
  activeGateCount: number
  recentGates: { name: string; category: string; createdAt: string }[]
  totalLives: number
  totalDeads: number
  userCredits: number
  userTelegram: string
  userRank: string
  gatesByCategory: { category: string; count: number; lives: number; deads: number }[]
  topGates: { name: string; lives: number; deads: number; successRate: number }[]
  userCreated: string
}

const categoryMeta: Record<string, { icon: React.ElementType; color: string }> = {
}

function MatrixRain({ className = '' }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const cvs = canvasRef.current
    if (!cvs) return
    const c = cvs.getContext('2d')
    if (!c) return

    const chars = '0123456789'
    const columns: number[] = []

    function resize(canvas: HTMLCanvasElement) {
      const parent = canvas.parentElement!
      canvas.width = parent.offsetWidth
      canvas.height = parent.offsetHeight
      const colCount = Math.floor(canvas.width / 20)
      columns.length = 0
      for (let i = 0; i < colCount; i++) {
        columns.push(Math.random() * canvas.height)
      }
    }

    function draw(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) {
      ctx.fillStyle = 'rgba(5, 5, 5, 0.05)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.font = '12px monospace'

      for (let i = 0; i < columns.length; i++) {
        const x = i * 20
        columns[i] += 10
        if (columns[i] > canvas.height) columns[i] = 0
        ctx.fillStyle = `rgba(220, 38, 38, ${0.08 + Math.random() * 0.07})`
        ctx.fillText(chars[Math.floor(Math.random() * chars.length)], x, columns[i])
      }
    }

    resize(cvs)
    const ro = new ResizeObserver(() => resize(cvs))
    ro.observe(cvs.parentElement!)
    const interval = setInterval(() => {
      draw(cvs, c)
    }, 80)

    return () => {
      clearInterval(interval)
      ro.disconnect()
    }
  }, [])

  return <canvas ref={canvasRef} className={`absolute inset-0 pointer-events-none ${className}`} />
}

function StatCard({ title, value, subtitle, icon: Icon, color }: { title: string; value: string; subtitle?: string; icon: React.ElementType; color: string }) {

  return (
    <div className="group relative overflow-hidden rounded-lg border border-red-900/30 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-5 transition-all duration-500 hover:border-red-600/60 hover:shadow-[0_0_30px_rgba(220,38,38,0.15)] hover:-translate-y-0.5">
      <div className="absolute left-0 top-0 h-8 w-8">
        <svg viewBox="0 0 32 32" className="h-full w-full">
          <path d="M0,0 L12,0 L12,2 L2,2 L2,12 L0,12 Z" fill="rgba(220, 38, 38, 0.3)" />
        </svg>
      </div>
      <div className="absolute bottom-0 right-0 h-8 w-8 rotate-180">
        <svg viewBox="0 0 32 32" className="h-full w-full">
          <path d="M0,0 L12,0 L12,2 L2,2 L2,12 L0,12 Z" fill="rgba(220, 38, 38, 0.2)" />
        </svg>
      </div>
      <div className="absolute inset-0 bg-gradient-to-r from-red-600/0 via-red-600/5 to-red-600/0 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-500/40 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-red-500/10 to-transparent" />
      <div className="absolute top-0 right-0 w-20 h-20 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-all duration-500" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-gray-500">{title}</p>
          <p className="mt-2 font-mono text-3xl font-bold text-white tabular-nums">{value}</p>
          {subtitle && <p className="mt-1 font-mono text-sm text-emerald-400">{subtitle}</p>}
        </div>
        <div className="relative flex h-14 w-14 items-center justify-center">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 56 56">
            <path d="M28,2 L52,15 L52,41 L28,54 L4,41 L4,15 Z" fill="rgba(220, 38, 38, 0.1)" stroke="rgba(220, 38, 38, 0.3)" strokeWidth="1" />
          </svg>
          <Icon className={`relative z-10 h-6 w-6 ${color} group-hover:scale-110 transition-transform duration-300`} />
        </div>
      </div>
      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-red-900/30 to-transparent" />
    </div>
  )
}

function PulseDot({ color = 'green' }: { color?: string }) {
  const dotClass = color === 'green' ? 'bg-green-500' : 'bg-red-500'
  return (
    <span className={`inline-flex h-2 w-2 rounded-full ${dotClass}`} />
  )
}

function Panel({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border border-red-900/30 bg-[#0a0a0f] overflow-hidden">{children}</div>
}

export default function DashboardPage() {
  const { data: session } = useSession()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/dashboard')
        if (!res.ok) return
        const json = await res.json()
        setData({
          userCount: json.userCount,
          recentUsers: json.recentUsers,
          topUsers: json.topUsers,
          gateCount: json.gateCount,
          activeGateCount: json.activeGateCount,
          recentGates: json.recentGates,
          totalLives: json.totalLives,
          totalDeads: json.totalDeads,
          userCredits: json.userCredits,
          userTelegram: json.userTelegram,
          userRank: json.userRank,
          gatesByCategory: json.gatesByCategory,
          topGates: json.topGates,
          userCreated: json.userCreated,
        })
      } catch { }
      setLoading(false)
    }
    fetchData()
  }, [session])

  const totalChecks = (data?.totalLives ?? 0) + (data?.totalDeads ?? 0)
  const successRate = totalChecks > 0 ? Math.round(((data?.totalLives ?? 0) / totalChecks) * 100) : 0

  const animatedLives = useCounter(data?.totalLives ?? 0)
  const animatedDeads = useCounter(data?.totalDeads ?? 0)
  const animatedTotal = useCounter(totalChecks)
  const animatedRate = useCounter(successRate)
  const animatedUsers = useCounter(data?.userCount ?? 0)
  const animatedGates = useCounter(data?.activeGateCount ?? 0)
  const animatedCredits = useCounter(data?.userCredits ?? 0)

  if (loading) return (
    <div className="rounded-xl border border-red-900/20 bg-black/60 p-12 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        <span className="font-mono-cyber text-xs text-red-400">CARGANDO SISTEMA...</span>
      </div>
    </div>
  )

  return (
    <div className="relative">
      {/* welcome toast */}

      <DashboardParticles />
      <MatrixRain className="opacity-30" />

      <div className="relative z-10 space-y-6">
        {/* Top Stats Row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="USUARIOS" value={String(animatedUsers)} subtitle={`${data?.recentUsers.length ?? 0} nuevos`} icon={Users} color="text-red-500" />
          <StatCard title="GATES ACTIVOS" value={String(animatedGates)} subtitle={`de ${data?.gateCount ?? 0} totales`} icon={Activity} color="text-red-500" />
          <StatCard title="MIS CRÉDITOS" value={String(animatedCredits)} subtitle={`Rango: ${data?.userRank ?? 'user'}`} icon={Zap} color="text-red-500" />
          <StatCard title="SUCCESS RATE" value={`${animatedRate}%`} subtitle={`${totalChecks} verificaciones`} icon={BarChart3} color="text-red-500" />
        </div>

        {/* Second Row: Global Stats + Right Column */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Global Stats */}
          <Panel>
            <div className="relative overflow-hidden rounded-lg bg-[#0a0a0f] p-6">
              <div className="opacity-20" />
              <div className="relative z-10">
                <h2 className="mb-4 font-mono-cyber text-sm font-bold uppercase tracking-[0.2em] text-red-400 border-b border-red-900/50 pb-3 flex items-center gap-2">
                  <Terminal className="h-4 w-4" /> <span>Estadísticas Globales</span>
                </h2>
                <div className="grid grid-cols-3 gap-3">
                  <div className="border border-green-900/40 bg-green-950/20 p-4 cyber-clip-alt text-center">
                    <p className="font-mono-cyber text-2xl font-black text-green-400 tabular-nums">{animatedLives}</p>
                    <p className="font-mono-cyber text-[10px] uppercase text-green-700 mt-1 flex items-center justify-center gap-1"><CheckCircle2 className="h-3 w-3" /> Live</p>
                  </div>
                  <div className="border border-red-900/40 bg-red-950/20 p-4 cyber-clip-alt text-center">
                    <p className="font-mono-cyber text-2xl font-black text-red-500 tabular-nums">{animatedDeads}</p>
                    <p className="font-mono-cyber text-[10px] uppercase text-red-700 mt-1 flex items-center justify-center gap-1"><XCircle className="h-3 w-3" /> Dead</p>
                  </div>
                  <div className="border border-blue-900/40 bg-blue-950/20 p-4 cyber-clip-alt text-center">
                    <p className="font-mono-cyber text-2xl font-black text-blue-400 tabular-nums">{animatedTotal}</p>
                    <p className="font-mono-cyber text-[10px] uppercase text-blue-700 mt-1 flex items-center justify-center gap-1"><Activity className="h-3 w-3" /> Total</p>
                  </div>
                  <div className="col-span-3 border border-gray-700 bg-gray-900/40 p-4 cyber-clip-alt">
                    <div className="flex items-center justify-center gap-4">
                      <div className="flex-1">
                        <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full transition-all duration-1000" style={{ width: `${successRate}%` }} />
                        </div>
                      </div>
                      <span className="font-mono-cyber text-2xl font-black text-white tabular-nums">{animatedRate}%</span>
                      <span className="font-mono-cyber text-[10px] uppercase text-gray-500">Success Rate</span>
                    </div>
                  </div>
                </div>

                <h3 className="mt-4 mb-2 font-mono-cyber text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500 flex items-center gap-2">
                  <span className="h-px flex-1 bg-red-900/30" />
                  Gates por Categoría
                  <span className="h-px flex-1 bg-red-900/30" />
                </h3>
                <div className="space-y-1.5">
                  {data?.gatesByCategory.map(({ category, count, lives, deads }) => {
                    const meta = categoryMeta[category]
                    const Icon = meta?.icon ?? Terminal
                    const sr = lives + deads > 0 ? Math.round((lives / (lives + deads)) * 100) : 0
                    return (
                      <div key={category} className="group/cat flex items-center gap-3 border border-gray-800 bg-black/50 px-3 py-2 hover:border-red-800/50 hover:bg-red-950/10 transition-all duration-300">
                        <Icon className={`h-4 w-4 shrink-0 ${meta?.color ?? 'text-gray-400'} group-hover/cat:scale-110 transition-transform`} />
                        <div className="flex-1 min-w-0">
                          <p className="font-mono-cyber text-xs text-white uppercase truncate">{category}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-green-500">{lives}L</span>
                            <span className="text-[10px] text-red-500">{deads}D</span>
                            <span className="text-[10px] text-gray-600">|</span>
                            <span className={`text-[10px] ${sr >= 50 ? 'text-green-500' : sr > 0 ? 'text-yellow-500' : 'text-gray-600'}`}>{sr}%</span>
                          </div>
                        </div>
                        <span className="font-mono-cyber text-xs text-gray-500">{count} gates</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </Panel>

          <div className="space-y-4">
            {/* Top Gates */}
            <Panel>
              <div className="relative overflow-hidden rounded-lg bg-[#0a0a0f] p-6">
                <div className="relative z-10">
                  <h2 className="mb-3 font-mono-cyber text-sm font-bold uppercase tracking-[0.2em] text-red-400 border-b border-red-900/50 pb-3 flex items-center gap-2">
                    <Globe className="h-4 w-4" /> <span>Top Gates por Live</span>
                  </h2>
                  <div className="space-y-1.5">
                    {data?.topGates.map((g, i) => (
                      <div key={i} className="group/gate flex items-center gap-3 border border-gray-800 bg-black/50 px-3 py-2 hover:border-green-800/40 hover:bg-green-950/10 transition-all duration-300">
                        <span className="font-mono-cyber text-lg font-black text-gray-600 w-6 group-hover/gate:text-red-500 transition-colors">#{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-mono-cyber text-xs text-white truncate">{g.name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-green-500">{g.lives}L</span>
                            <span className="text-[10px] text-red-500">{g.deads}D</span>
                          </div>
                        </div>
                        <span className={`font-mono-cyber text-xs font-bold ${g.successRate >= 50 ? 'text-green-400' : g.successRate > 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                          {g.successRate}%
                        </span>
                      </div>
                    ))}
                    {(data?.topGates.length ?? 0) === 0 && (
                      <p className="font-mono-cyber text-xs text-gray-600 italic">Aún no hay verificaciones</p>
                    )}
                  </div>
                </div>
              </div>
            </Panel>

            {/* Top Users */}
            <Panel>
              <div className="relative overflow-hidden rounded-lg bg-[#0a0a0f] p-6">
                <div className="relative z-10">
                  <h2 className="mb-3 font-mono-cyber text-sm font-bold uppercase tracking-[0.2em] text-red-400 border-b border-red-900/50 pb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" /> <span>Top Usuarios por Live</span>
                  </h2>
                  <div className="space-y-1.5">
                    {data?.topUsers.map((u, i) => (
                      <div key={i} className="group/user flex items-center gap-3 border border-gray-800 bg-black/50 px-3 py-2 hover:border-yellow-800/40 hover:bg-yellow-950/10 transition-all duration-300">
                        <span className="font-mono-cyber text-lg font-black text-gray-600 w-6 group-hover/user:text-yellow-500 transition-colors">#{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-mono-cyber text-xs text-white truncate">{u.username}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-green-500">{u.lives}L</span>
                            <span className="text-[10px] text-red-500">{u.deads}D</span>
                          </div>
                        </div>
                        <span className={`font-mono-cyber text-xs font-bold ${u.rank === 'admin' ? 'text-yellow-400' : 'text-gray-500'}`}>
                          {u.rank}
                        </span>
                      </div>
                    ))}
                    {(data?.topUsers.length ?? 0) === 0 && (
                      <p className="font-mono-cyber text-xs text-gray-600 italic">Aún no hay actividad</p>
                    )}
                  </div>
                </div>
              </div>
            </Panel>
          </div>
        </div>

        {/* Actividad Reciente */}
        <Panel>
          <div className="relative overflow-hidden rounded-lg bg-[#0a0a0f] p-6">
            <div className="relative z-10">
              <h2 className="mb-3 font-mono-cyber text-sm font-bold uppercase tracking-[0.2em] text-red-400 border-b border-red-900/50 pb-3 flex items-center gap-2">
                <Activity className="h-4 w-4" /> <span>Actividad Reciente</span>
              </h2>
              <div className="space-y-2">
                <div>
                  <p className="mb-1.5 font-mono-cyber text-[10px] font-bold uppercase tracking-widest text-blue-400 flex items-center gap-1">
                    <UserPlus className="h-3 w-3" /> Nuevos Usuarios
                  </p>
                  {data?.recentUsers.length ? (
                    <div className="space-y-1">
                      {data.recentUsers.map((u, i) => (
                        <div key={i} className="flex items-center justify-between border border-gray-800 bg-black/50 px-3 py-1.5 hover:border-blue-800/40 transition-colors">
                          <span className="font-mono-cyber text-xs text-green-400">{u.username}</span>
                          <span className="font-mono-cyber text-[10px] text-gray-600">
                            {new Date(u.createdAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="font-mono-cyber text-[10px] text-gray-600 italic">Sin usuarios recientes</p>
                  )}
                </div>
                <div>
                  <p className="mb-1.5 font-mono-cyber text-[10px] font-bold uppercase tracking-widest text-orange-400 flex items-center gap-1 mt-3">
                    <Plus className="h-3 w-3" /> Nuevos Gates
                  </p>
                  {data?.recentGates.length ? (
                    <div className="space-y-1">
                      {data.recentGates.map((g, i) => {
                        const meta = categoryMeta[g.category]
                        const Icon = meta?.icon ?? Terminal
                        return (
                          <div key={i} className="flex items-center justify-between border border-gray-800 bg-black/50 px-3 py-1.5 hover:border-orange-800/40 transition-colors">
                            <div className="flex items-center gap-2">
                              <Icon className={`h-3 w-3 ${meta?.color ?? 'text-gray-400'}`} />
                              <span className="font-mono-cyber text-xs text-white">{g.name}</span>
                            </div>
                            <span className="font-mono-cyber text-[10px] text-gray-600">
                              {new Date(g.createdAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="font-mono-cyber text-[10px] text-gray-600 italic">Sin gates recientes</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Panel>

        {/* System Status */}
        <Panel>
          <div className="relative overflow-hidden rounded-lg bg-[#0a0a0f] p-6">
            <div className="relative z-10">
              <h2 className="mb-4 font-mono-cyber text-sm font-bold uppercase tracking-[0.2em] text-red-400 border-b border-red-900/50 pb-3 flex items-center gap-2">
                <Terminal className="h-4 w-4" /> <span>Estado del Sistema</span>
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="border border-green-900/40 bg-green-950/20 p-4 cyber-clip-alt">
                  <div className="flex items-center gap-2 mb-2">
                    <PulseDot color="green" />
                    <span className="font-mono-cyber text-[10px] font-bold uppercase text-green-400">Base de Datos</span>
                  </div>
                  <p className="font-mono-cyber text-xs text-gray-400">{data?.userCount ?? 0} usuarios · {data?.gateCount ?? 0} gates</p>
                </div>
                <div className="border border-green-900/40 bg-green-950/20 p-4 cyber-clip-alt">
                  <div className="flex items-center gap-2 mb-2">
                    <PulseDot color="green" />
                    <span className="font-mono-cyber text-[10px] font-bold uppercase text-green-400">API Gateway</span>
                  </div>
                  <p className="font-mono-cyber text-xs text-gray-400">{data?.activeGateCount ?? 0} gates activos</p>
                </div>
                <div className="border border-green-900/40 bg-green-950/20 p-4 cyber-clip-alt">
                  <div className="flex items-center gap-2 mb-2">
                    <PulseDot color="green" />
                    <span className="font-mono-cyber text-[10px] font-bold uppercase text-green-400">Autenticación</span>
                  </div>
                  <p className="font-mono-cyber text-xs text-gray-400">SSL/TLS</p>
                </div>
                <div className="border border-green-900/40 bg-green-950/20 p-4 cyber-clip-alt">
                  <div className="flex items-center gap-2 mb-2">
                    <PulseDot color="green" />
                    <span className="font-mono-cyber text-[10px] font-bold uppercase text-green-400">Servidor</span>
                  </div>
                  <p className="font-mono-cyber text-xs text-gray-400">{totalChecks} verificaciones totales</p>
                </div>
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}
