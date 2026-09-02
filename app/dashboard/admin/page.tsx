'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSession } from 'next-auth/react'
import { Terminal, Zap, Users, Shield, Activity, CheckCircle2, XCircle, ArrowRight, CreditCard, Globe, KeyRound } from 'lucide-react'

interface AdminStats {
  gates: unknown[]
  totalGates: number
  totalCreditsLive: number
  totalCreditsDead: number
}

export default function AdminDashboardPage() {
  const { data: session } = useSession()
  const rank = session?.user?.rank
  const isAdmin = rank === 'admin'
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [users, setUsers] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchStats() {
      try {
        const [gatesRes, usersRes] = await Promise.all([
          fetch('/api/admin/gates'),
          fetch('/api/admin/usuarios'),
        ])
        if (gatesRes.ok) {
          const gatesData = await gatesRes.json()
          setStats(gatesData)
        }
        if (usersRes.ok) {
          const usersData = await usersRes.json()
          setUsers(usersData.length)
        }
      } catch { }
      setLoading(false)
    }
    if (isAdmin) fetchStats()
    else setLoading(false)
  }, [isAdmin])

  if (loading) return <div className="matrix-bg rounded-xl min-h-[300px]" />

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="relative overflow-hidden cyber-clip border border-purple-500/30 bg-black/80 p-4">
          <div className="flex items-center gap-4">
            <div className="p-3 border border-purple-500/30 bg-purple-950/40"><Shield className="h-6 w-6 text-purple-400" /></div>
            <div>
              <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">Total Gates</p>
              <p className="font-mono-cyber text-3xl font-black text-white">{stats?.totalGates ?? 0}</p>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden cyber-clip border border-green-500/30 bg-black/80 p-4">
          <div className="flex items-center gap-4">
            <div className="p-3 border border-green-500/30 bg-green-950/40"><CheckCircle2 className="h-6 w-6 text-green-400" /></div>
            <div>
              <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">Costo Live</p>
              <p className="font-mono-cyber text-3xl font-black text-green-400">{stats?.totalCreditsLive ?? 0}</p>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden cyber-clip border border-purple-500/30 bg-black/80 p-4">
          <div className="flex items-center gap-4">
            <div className="p-3 border border-purple-500/30 bg-purple-950/40"><XCircle className="h-6 w-6 text-purple-500" /></div>
            <div>
              <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">Costo Dead</p>
              <p className="font-mono-cyber text-3xl font-black text-purple-500">{stats?.totalCreditsDead ?? 0}</p>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden cyber-clip border border-blue-500/30 bg-black/80 p-4">
          <div className="flex items-center gap-4">
            <div className="p-3 border border-blue-500/30 bg-blue-950/40"><Activity className="h-6 w-6 text-blue-400" /></div>
            <div>
              <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">Total Usuarios</p>
              <p className="font-mono-cyber text-3xl font-black text-blue-400">{users ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {isAdmin && (
          <Link href="/dashboard/admin/gates"
            className="cyber-clip border border-purple-500/30 bg-black/80 p-6 group hover:border-purple-500/60 transition-all cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CreditCard className="h-8 w-8 text-purple-400" />
                <div>
                  <h3 className="font-mono-cyber text-sm font-bold text-white uppercase tracking-widest">Gestión de Gates</h3>
                  <p className="font-mono-cyber text-xs text-gray-500 mt-1">Administra costos, estados y estadísticas</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-purple-500 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
            </div>
          </Link>
        )}

        {(isAdmin || rank === 'moderador') && (
          <Link href="/dashboard/admin/usuarios"
            className="cyber-clip border border-purple-500/30 bg-black/80 p-6 group hover:border-purple-500/60 transition-all cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Users className="h-8 w-8 text-purple-400" />
                <div>
                  <h3 className="font-mono-cyber text-sm font-bold text-white uppercase tracking-widest">Gestión de Usuarios</h3>
                  <p className="font-mono-cyber text-xs text-gray-500 mt-1">Administra créditos, rangos y membresías</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-purple-500 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
            </div>
          </Link>
        )}

        <Link href="/dashboard/admin/keys"
          className="cyber-clip border border-purple-500/30 bg-black/80 p-6 group hover:border-purple-500/60 transition-all cursor-pointer">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <KeyRound className="h-8 w-8 text-purple-400" />
              <div>
                <h3 className="font-mono-cyber text-sm font-bold text-white uppercase tracking-widest">Gestión de Keys</h3>
                <p className="font-mono-cyber text-xs text-gray-500 mt-1">Genera y administra claves de activación</p>
              </div>
            </div>
            <ArrowRight className="h-5 w-5 text-purple-500 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
          </div>
        </Link>
      </div>
    </div>
  )
}
