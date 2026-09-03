'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import {
  Cookie,
  Copy,
  CheckCircle2,
  RefreshCw,
  Globe,
  Zap,
  Trash2,
} from 'lucide-react'
import { toast } from '@/lib/toast'
import { useRouter } from 'next/navigation'

const COUNTRIES = [
  { code: 'US', name: '🇺🇸 Estados Unidos', flag: 'US' },
  { code: 'MX', name: '🇲🇽 México', flag: 'MX' },
  { code: 'CA', name: '🇨🇦 Canadá', flag: 'CA' },
  { code: 'BR', name: '🇧🇷 Brasil', flag: 'BR' },
  { code: 'DE', name: '🇩🇪 Alemania', flag: 'DE' },
  { code: 'ES', name: '🇪🇸 España', flag: 'ES' },
  { code: 'IT', name: '🇮🇹 Italia', flag: 'IT' },
  { code: 'FR', name: '🇫🇷 Francia', flag: 'FR' },
  { code: 'UK', name: '🇬🇧 Reino Unido', flag: 'GB' },
  { code: 'NL', name: '🇳🇱 Países Bajos', flag: 'NL' },
  { code: 'JP', name: '🇯🇵 Japón', flag: 'JP' },
  { code: 'AU', name: '🇦🇺 Australia', flag: 'AU' },
  { code: 'IN', name: '🇮🇳 India', flag: 'IN' },
  { code: 'SG', name: '🇸🇬 Singapur', flag: 'SG' },
  { code: 'AE', name: '🇦🇪 EAU', flag: 'AE' },
  { code: 'SA', name: '🇸🇦 Arabia Saudita', flag: 'SA' },
  { code: 'TR', name: '🇹🇷 Turquía', flag: 'TR' },
  { code: 'SE', name: '🇸🇪 Suecia', flag: 'SE' },
  { code: 'PL', name: '🇵🇱 Polonia', flag: 'PL' },
  { code: 'EG', name: '🇪🇬 Egipto', flag: 'EG' },
]

const COST = 25

export default function AmazonCookiesPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  const [selectedCountry, setSelectedCountry] = useState('US')
  const [generating, setGenerating] = useState(false)
  const [cookie, setCookie] = useState('')
  const [profile, setProfile] = useState<{ name?: string; email?: string; password?: string } | null>(null)
  const [timeTaken, setTimeTaken] = useState('')
  const [copied, setCopied] = useState(false)
  const [credits, setCredits] = useState<number | null>(null)

  const rank = session?.user?.rank as string | undefined
  const ALLOWED = ['premium', 'vip', 'seller', 'moderador', 'admin']
  const allowed = rank ? ALLOWED.includes(rank) : false

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/auth/login'); return }
    if (!allowed) router.push('/dashboard')
  }, [session, status, allowed, router])

  const generateCookie = async () => {
    if (generating) return
    setGenerating(true)
    setCookie('')
    setProfile(null)
    setTimeTaken('')
    try {
      const res = await fetch('/api/tools/amazon-cookie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country: selectedCountry }),
      })
      const data = await res.json()

      if (data.error) {
        toast.error(data.error, { description: data.creditsRemaining !== undefined ? `Credits: ${data.creditsRemaining}` : undefined })
        if (data.creditsRemaining !== undefined) setCredits(data.creditsRemaining)
        return
      }

      setCookie(data.cookies)
      setProfile(data.profile)
      setTimeTaken(data.time_taken || '')
      if (data.creditsRemaining !== undefined) setCredits(data.creditsRemaining)
      toast.success('Cookie generada exitosamente', { description: data.creditsRemaining !== undefined ? `${data.creditsDeducted} credits descontados` : undefined })
    } catch {
      toast.error('Error al generar cookie')
    } finally {
      setGenerating(false)
    }
  }

  const copyCookie = async () => {
    if (!cookie) return
    await navigator.clipboard.writeText(cookie)
    setCopied(true)
    toast.success('Cookie copiada al portapapeles')
    setTimeout(() => setCopied(false), 2000)
  }

  const clearCookie = () => {
    setCookie('')
    setProfile(null)
    setTimeTaken('')
    setCopied(false)
    toast.info('Cookie limpiada')
  }

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!allowed) return null

  return (
    <div className="space-y-6 matrix-bg min-h-screen rounded-xl border border-purple-900/30 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-purple-500/20 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Cookie className="h-10 w-10 text-purple-500 animate-pulse-glow" />
            <h1 className="text-4xl font-black uppercase tracking-widest text-white neon-text-purple">
              AMAZON COOKIES
            </h1>
          </div>
          <p className="mt-2 font-mono-cyber text-sm text-purple-500/80 uppercase">
            &gt; Generador de cookies Amazon — USA &amp; 19 países
          </p>
        </div>
        <div className="flex items-center gap-4">
          {credits !== null && (
            <div className="flex items-center gap-2 border border-purple-500/30 bg-purple-950/30 px-4 py-2">
              <span className="font-mono-cyber text-xs text-purple-400">CREDITS:</span>
              <span className="font-mono-cyber text-lg font-black text-white">{credits}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">COSTO:</span>
            <span className="font-mono-cyber text-xs font-bold text-purple-400 border border-purple-500/30 bg-purple-950/30 px-2 py-0.5">
              {COST} credits/cookie
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">RANGO:</span>
            <span className="font-mono-cyber text-xs font-bold text-purple-400 border border-purple-500/30 bg-purple-950/30 px-2 py-0.5">
              {rank?.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Country selector + Generate */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
        <div className="flex-1 w-full sm:w-auto space-y-1">
          <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">PAÍS</p>
          <div className="flex items-center gap-2">
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              disabled={generating}
              className="w-full sm:w-64 bg-black border border-gray-700 text-gray-300 font-mono-cyber text-xs px-3 py-2.5 focus:outline-none focus:border-purple-500/50 disabled:opacity-50"
            >
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
            <Globe className="h-4 w-4 text-purple-500" />
          </div>
        </div>

        <button
          onClick={generateCookie}
          disabled={generating}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-mono-cyber text-sm font-bold uppercase px-6 py-2.5 transition-all duration-200 shadow-[0_0_15px_rgba(168,85,247,0.4)] hover:shadow-[0_0_25px_rgba(168,85,247,0.6)] cursor-pointer"
        >
          {generating ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Zap className="h-4 w-4" />
          )}
          {generating ? 'GENERANDO...' : 'GENERAR COOKIE'}
        </button>
      </div>

      {/* Cookie display */}
      {cookie && (
        <div className="space-y-4">
          {/* Profile card */}
          {profile && (
            <div className="border border-green-500/30 bg-black/80 p-4">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-green-500/60 to-transparent" />
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500 mb-1">EMAIL</p>
                  <p className="font-mono-cyber text-sm text-green-400 truncate">{profile.email}</p>
                </div>
                <div>
                  <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500 mb-1">PASSWORD</p>
                  <p className="font-mono-cyber text-sm text-green-400">{profile.password}</p>
                </div>
                <div>
                  <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500 mb-1">TIEMPO</p>
                  <p className="font-mono-cyber text-sm text-green-400">{timeTaken}s</p>
                </div>
              </div>
            </div>
          )}

          {/* Cookie textarea */}
          <div className="border border-purple-500/30 bg-black/80 p-4 relative">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-500/60 to-transparent" />
            <div className="flex items-center justify-between mb-3">
              <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">TU COOKIE AMAZON</p>
              <div className="flex items-center gap-2">
                <button
                  onClick={copyCookie}
                  className="flex items-center gap-1.5 border border-gray-700 hover:border-purple-500/50 bg-black/50 px-3 py-1.5 text-xs font-mono-cyber text-gray-400 hover:text-white transition-all duration-200 cursor-pointer"
                >
                  {copied ? (
                    <CheckCircle2 className="h-3 w-3 text-green-400" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  {copied ? 'COPIADO' : 'COPIAR'}
                </button>
                <button
                  onClick={clearCookie}
                  className="flex items-center gap-1.5 border border-gray-700 hover:border-red-500/50 bg-black/50 px-3 py-1.5 text-xs font-mono-cyber text-gray-400 hover:text-red-400 transition-all duration-200 cursor-pointer"
                >
                  <Trash2 className="h-3 w-3" />
                  LIMPIAR
                </button>
              </div>
            </div>
            <textarea
              readOnly
              value={cookie}
              className="w-full h-48 bg-black/60 border border-gray-800 text-gray-300 font-mono-cyber text-xs p-3 resize-none focus:outline-none focus:border-purple-500/50"
              placeholder="La cookie aparecerá aquí..."
            />
          </div>

          {/* Info */}
          <div className="border border-yellow-900/30 bg-yellow-950/10 px-4 py-3">
            <p className="font-mono-cyber text-[10px] text-yellow-400 uppercase tracking-widest mb-1">IMPORTANTE</p>
            <p className="font-mono-cyber text-xs text-yellow-500/70">
              Usa esta cookie en el gate Amazon (Cookie) para verificar tarjetas. La cookie expira en ~24h. Genera una nueva si deja de funcionar.
            </p>
          </div>
        </div>
      )}

      {/* Generator info */}
      {!cookie && !generating && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div className="border border-purple-500/30 bg-black/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-4 w-4 text-purple-400" />
              <span className="font-mono-cyber text-sm font-bold text-purple-400">Rápido</span>
            </div>
            <p className="font-mono-cyber text-[11px] text-gray-500 leading-relaxed">Generación en 10-30 segundos promedio</p>
          </div>
          <div className="border border-purple-500/30 bg-black/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Cookie className="h-4 w-4 text-purple-400" />
              <span className="font-mono-cyber text-sm font-bold text-purple-400">Sin Captcha</span>
            </div>
            <p className="font-mono-cyber text-[11px] text-gray-500 leading-relaxed">No dispara captcha de Amazon — funciona directo</p>
          </div>
          <div className="border border-purple-500/30 bg-black/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="h-4 w-4 text-purple-400" />
              <span className="font-mono-cyber text-sm font-bold text-purple-400">20 Países</span>
            </div>
            <p className="font-mono-cyber text-[11px] text-gray-500 leading-relaxed">USA, México, Europa, Asia y más</p>
          </div>
          <div className="border border-purple-500/30 bg-black/50 p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="h-4 w-4 text-purple-400" />
              <span className="font-mono-cyber text-sm font-bold text-purple-400">Cookie Real</span>
            </div>
            <p className="font-mono-cyber text-[11px] text-gray-500 leading-relaxed">Cookie auténtica de Amazon.com válida 24h</p>
          </div>
        </div>
      )}
    </div>
  )
}
