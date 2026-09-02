'use client'

import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { Zap, Shield, KeyRound } from 'lucide-react'
import Image from 'next/image'
import { toast } from '@/lib/toast'

interface ProfileData {
  id: string
  username: string
  telegramId: string
  rank: string
  credits: number
  membershipExpiresAt: string | null
  createdAt: string
}

export default function PerfilPage() {
  // const { data: session } = useSession()
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [redeemKey, setRedeemKey] = useState('')
  const [redeemLoading, setRedeemLoading] = useState(false)

  async function fetchProfile() {
    try {
      const res = await fetch('/api/user/profile')
      if (res.ok) {
        const data = await res.json()
        setProfile(data)
      }
    } catch { }
    setLoading(false)
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  async function handleRedeem(e: React.FormEvent) {
    e.preventDefault()
    if (!redeemKey.trim()) return

    setRedeemLoading(true)
    try {
      const res = await fetch('/api/user/redeem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: redeemKey }),
      })

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || 'Error al canjear la clave')
      } else {
        toast.success(`Clave canjeada: +${data.creditsAdded} créditos y +${data.daysAdded} días de membresía`)
        setRedeemKey('')
        window.dispatchEvent(new CustomEvent('credits-updated', { detail: data.finalCredits }))
        fetchProfile()
      }
    } catch {
      toast.error('Error al conectar con el servidor')
    } finally {
      setRedeemLoading(false)
    }
  }

  if (loading) return <div className="matrix-bg rounded-xl min-h-[500px]" />

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center border border-dashed border-purple-500/30 bg-purple-950/10 py-20 cyber-clip min-h-[500px] matrix-bg">
        <h3 className="font-mono-cyber text-lg font-bold text-purple-500 uppercase tracking-widest">ERROR: PERFIL NO ENCONTRADO</h3>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6 matrix-bg min-h-screen rounded-xl border border-purple-900/30">
      <div className="relative overflow-hidden cyber-clip border border-purple-500/50 bg-black/80">
        <div className="absolute inset-0 bg-gradient-to-r from-black via-purple-950/40 to-black/90" />
        <div className="relative flex flex-col md:flex-row items-center gap-8 p-8 z-10">
          <div className="relative h-28 w-28 cyber-clip border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.3)] overflow-hidden">
            <Image src="/images/avatar-capitan-black.jpg" alt="Avatar" fill className="object-cover" />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-4xl font-black uppercase tracking-widest text-white neon-text-purple">{profile.username}</h1>
            <div className="mt-2 flex flex-wrap items-center justify-center md:justify-start gap-3">
              <span className={`inline-flex items-center gap-1 border px-3 py-1 font-mono-cyber text-xs uppercase ${profile.rank === 'admin' ? 'border-purple-500/30 bg-purple-950/40 text-purple-400' :
                profile.rank === 'moderador' ? 'border-purple-500/30 bg-purple-950/40 text-purple-400' :
                  profile.rank === 'seller' ? 'border-blue-500/30 bg-blue-950/40 text-blue-400' :
                    profile.rank === 'vip' ? 'border-yellow-500/30 bg-yellow-950/40 text-yellow-400' :
                      profile.rank === 'premium' ? 'border-green-500/30 bg-green-950/40 text-green-400' :
                        profile.rank === 'baneado' ? 'border-purple-500/30 bg-purple-950/40 text-purple-600' :
                          'border-purple-500/30 bg-purple-950/40 text-purple-400'
                }`}>
                <Shield className="h-3 w-3" /> {profile.rank}
              </span>
              <span className="inline-flex items-center gap-1 border border-yellow-500/30 bg-yellow-950/40 px-3 py-1 font-mono-cyber text-xs text-yellow-400">
                <Zap className="h-3 w-3" /> {profile.credits} CRÉDITOS
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="cyber-clip border border-purple-500/30 bg-black/80 p-6 space-y-4">
          <h2 className="font-mono-cyber text-sm font-bold uppercase tracking-widest text-purple-400 border-b border-purple-900/50 pb-3">
            INFORMACIÓN DE CUENTA
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">ID</span>
              <span className="font-mono-cyber text-xs text-gray-300">{profile.id}</span>
            </div>
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Usuario</span>
              <span className="font-mono-cyber text-xs text-green-400">{profile.username}</span>
            </div>
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Telegram ID</span>
              <span className="font-mono-cyber text-xs text-blue-400">{profile.telegramId || '—'}</span>
            </div>
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Rango</span>
              <span className={`font-mono-cyber text-xs uppercase ${profile.rank === 'admin' ? 'text-purple-400' :
                profile.rank === 'moderador' ? 'text-purple-400' :
                  profile.rank === 'seller' ? 'text-blue-400' :
                    profile.rank === 'vip' ? 'text-yellow-400' :
                      profile.rank === 'premium' ? 'text-green-400' :
                        profile.rank === 'baneado' ? 'text-purple-600' :
                          'text-gray-400'
                }`}>{profile.rank}</span>
            </div>
          </div>
        </div>

        <div className="cyber-clip border border-purple-500/30 bg-black/80 p-6 space-y-4">
          <h2 className="font-mono-cyber text-sm font-bold uppercase tracking-widest text-purple-400 border-b border-purple-900/50 pb-3">
            ESTADO DE CUENTA
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Créditos</span>
              <span className="font-mono-cyber text-sm font-bold text-yellow-400">{profile.credits}</span>
            </div>
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Membresía expira</span>
              <span className="font-mono-cyber text-xs text-gray-300">
                {['admin', 'seller', 'moderador'].includes(profile.rank)
                  ? 'No expira'
                  : profile.membershipExpiresAt
                    ? new Date(profile.membershipExpiresAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })
                    : 'Sin membresía'}
              </span>
            </div>
            <div className="flex items-center justify-between border border-gray-800 bg-black/50 px-4 py-3">
              <span className="font-mono-cyber text-xs text-gray-500 uppercase">Registrado</span>
              <span className="font-mono-cyber text-xs text-gray-300">
                {new Date(profile.createdAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="cyber-clip border border-purple-500/30 bg-black/80 p-6 space-y-4">
        <h2 className="font-mono-cyber text-sm font-bold uppercase tracking-widest text-purple-400 border-b border-purple-900/50 pb-3 flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-purple-400" />
          <span>CANJEAR CLAVE DE ACTIVACIÓN</span>
        </h2>
        <form onSubmit={handleRedeem} className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            value={redeemKey}
            onChange={(e) => setRedeemKey(e.target.value)}
            placeholder="TRBL-XXXX-XXXX-XXXX"
            className="flex-1 h-12 border border-purple-900/50 bg-black/50 px-4 font-mono-cyber text-sm text-white placeholder-purple-900/30 focus:border-purple-500 focus:outline-none"
            required
            disabled={redeemLoading}
          />
          <button
            type="submit"
            className="h-12 px-6 cyber-clip-alt bg-gradient-to-r from-purple-700 to-purple-600 font-mono-cyber text-xs font-bold tracking-widest text-white shadow-lg shadow-purple-900/50 hover:from-purple-600 hover:to-purple-500 transition-all cursor-pointer whitespace-nowrap"
            disabled={redeemLoading}
          >
            {redeemLoading ? 'PROCESANDO...' : 'CANJEAR CLAVE'}
          </button>
        </form>
        <p className="font-mono-cyber text-[10px] text-gray-500 uppercase tracking-wider">
          &gt; El canje de keys sumará créditos y días de membresía de forma automática.
        </p>
      </div>
    </div>
  )
}
