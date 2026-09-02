'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useSession } from 'next-auth/react'
import {
  Mail,
  RefreshCw,
  Copy,
  Inbox,
  Eye,
  ArrowLeft,
  Zap,
  Globe,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Terminal,
  Trash2,
  Clock,
} from 'lucide-react'
import { toast } from '@/lib/toast'
import { useRouter } from 'next/navigation'

type Service = 'mailtm' | 'guerrillamail' | 'tempmail_lol' | 'dropmail'

interface MailAccount {
  service: Service
  email: string
  type: 'jwt' | 'sid' | 'token' | 'dropmail'
  token?: string
  password?: string
  domain?: string
  sidToken?: string
  dropToken?: string
  sessionId?: string
}

interface MailMessage {
  id: string
  from: { address: string; name?: string } | string
  subject: string
  date?: string
  createdAt?: string
  intro?: string
  seen?: boolean
  textBody?: string
  html?: string[]
}

interface DomainInfo {
  domain: string
  isActive: boolean
}

const GUERRILLA_DOMAINS = [
  'guerrillamail.com',
  'guerrillamail.net',
  'guerrillamail.org',
  'sharklasers.com',
  'guerrillamail.biz',
  'guerrillamailblock.com',
  'guerrillamail.de',
]

const serviceConfig: Record<Service, { name: string; color: string; border: string; badge: string; desc: string }> = {
  mailtm: {
    name: 'Mail.tm',
    color: 'text-orange-400',
    border: 'border-orange-500/40',
    badge: 'bg-orange-950/40 text-orange-400 border-orange-500/30',
    desc: 'API REST moderna con cuenta temporal',
  },
  guerrillamail: {
    name: 'Guerrilla Mail',
    color: 'text-green-400',
    border: 'border-green-500/40',
    badge: 'bg-green-950/40 text-green-400 border-green-500/30',
    desc: 'Sin registro, múltiples dominios, dura 1h',
  },
  tempmail_lol: {
    name: 'TempMail.lol',
    color: 'text-sky-400',
    border: 'border-sky-500/40',
    badge: 'bg-sky-950/40 text-sky-400 border-sky-500/30',
    desc: 'Sin registro, cuerpo completo en inbox',
  },
  dropmail: {
    name: 'DropMail.me',
    color: 'text-violet-400',
    border: 'border-violet-500/40',
    badge: 'bg-violet-950/40 text-violet-400 border-violet-500/30',
    desc: 'GraphQL, dominios dinámicos, hasta 30d',
  },
}

function fromAddress(from: MailMessage['from']): string {
  if (!from) return 'Desconocido'
  if (typeof from === 'string') return from
  return from.name ? `${from.name} <${from.address}>` : from.address
}

function timeAgo(date: string | undefined): string {
  if (!date) return ''
  const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  return `${Math.floor(diff / 3600)}h`
}

function formatDate(date: string | undefined): string {
  if (!date) return ''
  return new Date(date).toLocaleString('es-ES', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function TempMailPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  const [selectedService, setSelectedService] = useState<Service>('guerrillamail')
  const [domains, setDomains] = useState<DomainInfo[]>([])
  const [selectedDomain, setSelectedDomain] = useState<string>('')
  const [loadingDomains, setLoadingDomains] = useState(false)
  const [account, setAccount] = useState<MailAccount | null>(null)
  const [messages, setMessages] = useState<MailMessage[]>([])
  const [selectedMsg, setSelectedMsg] = useState<MailMessage | null>(null)
  const [fullMsg, setFullMsg] = useState<MailMessage | null>(null)
  const [generating, setGenerating] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState(false)
  const [copied, setCopied] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const refreshTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const rank = session?.user?.rank as string | undefined
  const ALLOWED = ['user', 'premium', 'vip', 'moderador', 'seller', 'admin']
  const allowed = rank ? ALLOWED.includes(rank) : false

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/auth/login'); return }
    if (!allowed) router.push('/dashboard')
  }, [session, status, allowed, router])

  // ─── Load saved account from DB on mount ───────────────────────

  useEffect(() => {
    if (status === 'loading' || !allowed) return
    ;(async () => {
      try {
        const res = await fetch('/api/tempmail/account')
        const data = await res.json()
        if (data.account && !data.error) {
          const a = data.account
          const acc: MailAccount = {
            service: a.service as Service,
            email: a.email,
            type: a.type as MailAccount['type'],
            token: a.token ?? undefined,
            password: a.password ?? undefined,
            domain: a.domain ?? undefined,
            sidToken: a.sidToken ?? undefined,
            dropToken: a.dropToken ?? undefined,
            sessionId: a.sessionId ?? undefined,
          }
          setAccount(acc)
          setSelectedService(acc.service)
          if (acc.domain) setSelectedDomain(acc.domain)
          else setSelectedDomain(acc.email.split('@')[1])
          // fetch inbox for restored account
          fetchInbox(acc)
        }
      } catch {
        // no saved account
      }
    })()
  }, [status, allowed]) // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Load domains when service changes ──────────────────────────

  const loadDomains = useCallback(async (service: Service) => {
    setLoadingDomains(true)
    if (service === 'guerrillamail') {
      setDomains(GUERRILLA_DOMAINS.map((d) => ({ domain: d, isActive: true })))
      setSelectedDomain(GUERRILLA_DOMAINS[0])
      setLoadingDomains(false)
      return
    }
    if (service === 'tempmail_lol' || service === 'dropmail') {
      setDomains([])
      setSelectedDomain('')
      setLoadingDomains(false)
      return
    }
    try {
      const res = await fetch('/api/tempmail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, action: 'domains', params: {} }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      const d: DomainInfo[] = data.domains ?? []
      setDomains(d)
      const active = d.find((x) => x.isActive)
      setSelectedDomain(active?.domain ?? d[0]?.domain ?? '')
    } catch {
      setDomains([])
    } finally {
      setLoadingDomains(false)
    }
  }, [])

  useEffect(() => {
    loadDomains(selectedService)
  }, [selectedService, loadDomains])

  // ─── Auto-refresh with cooldown ─────────────────────────────────

  const lastRefreshRef = useRef(0)

  const debouncedRefresh = useCallback((acc: MailAccount) => {
    const now = Date.now()
    if (now - lastRefreshRef.current < 6000) return
    lastRefreshRef.current = now
    if (refreshTimeoutRef.current) return
    refreshTimeoutRef.current = setTimeout(() => {
      refreshTimeoutRef.current = null
    }, 4000)
    fetchInbox(acc)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoRefresh && account) {
      intervalRef.current = setInterval(() => {
        if (!refreshTimeoutRef.current) {
          debouncedRefresh(account)
        }
      }, 15000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (refreshTimeoutRef.current) clearTimeout(refreshTimeoutRef.current)
    }
  }, [autoRefresh, account, debouncedRefresh])

  // ─── Generate ───────────────────────────────────────────────────

  const generateEmail = async () => {
    if (!selectedDomain && selectedService === 'mailtm') {
      toast.error('Selecciona un dominio primero')
      return
    }
    setGenerating(true)
    setMessages([])
    setSelectedMsg(null)
    setFullMsg(null)
    try {
      const params: Record<string, string> = {}
      if (selectedService === 'mailtm') {
        params.domain = selectedDomain
      }

      const res = await fetch('/api/tempmail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service: selectedService,
          action: 'generate',
          params,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

      let acc: MailAccount
      if (data.type === 'sid') {
        acc = {
          service: selectedService,
          email: data.email,
          type: 'sid',
          sidToken: data.sidToken,
        }
        setSelectedDomain(data.email.split('@')[1])
      } else if (data.type === 'token') {
        acc = {
          service: selectedService,
          email: data.email,
          type: 'token',
          token: data.token,
        }
        setSelectedDomain(data.email.split('@')[1])
      } else if (data.type === 'dropmail') {
        acc = {
          service: selectedService,
          email: data.email,
          type: 'dropmail',
          dropToken: data.dropToken,
          sessionId: data.sessionId,
        }
        setSelectedDomain(data.email.split('@')[1])
      } else {
        acc = {
          service: selectedService,
          email: data.email,
          type: 'jwt',
          token: data.token,
          password: data.password,
          domain: data.domain,
        }
      }
      setAccount(acc)
      // Save to DB
      fetch('/api/tempmail/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(acc),
      }).catch(() => {})
      toast.success('Correo temporal generado', { description: acc.email })
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error desconocido'
      toast.error('Error al generar correo', { description: msg })
    } finally {
      setGenerating(false)
    }
  }

  // ─── Fetch inbox ───────────────────────────────────────────────

  const fetchInbox = useCallback(async (acc: MailAccount) => {
    const now = Date.now()
    if (now - lastRefreshRef.current < 4000) {
      toast.info('Espera unos segundos antes de refrescar')
      return
    }
    lastRefreshRef.current = now
    setRefreshing(true)
    try {
      const params: Record<string, string> = {}
      if (acc.type === 'sid') {
        params.sidToken = acc.sidToken!
      } else if (acc.type === 'dropmail') {
        params.dropToken = acc.dropToken!
        params.sessionId = acc.sessionId!
      } else {
        params.token = acc.token!
      }
      const res = await fetch('/api/tempmail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service: acc.service,
          action: 'inbox',
          params,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setMessages(data.messages ?? [])
      if (data.sidToken) {
        setAccount((prev) => prev ? { ...prev, sidToken: data.sidToken } : prev)
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error desconocido'
      toast.error('Error al actualizar bandeja', { description: msg })
    } finally {
      setRefreshing(false)
    }
  }, [])

  // ─── Read message ──────────────────────────────────────────────

  const readMessage = async (msg: MailMessage) => {
    if (!account) return
    setSelectedMsg(msg)
    setLoadingMsg(true)
    setFullMsg(null)
    try {
      const params: Record<string, string> = { id: msg.id }
      if (account.type === 'sid') {
        params.sidToken = account.sidToken!
      } else if (account.type === 'dropmail') {
        params.dropToken = account.dropToken!
        params.sessionId = account.sessionId!
      } else {
        params.token = account.token!
      }
      const res = await fetch('/api/tempmail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service: account.service,
          action: 'read',
          params,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setFullMsg(data.message)
    } catch {
      toast.error('Error al leer mensaje')
    } finally {
      setLoadingMsg(false)
    }
  }

  // ─── Copy ──────────────────────────────────────────────────────

  const copyEmail = async () => {
    if (!account?.email) return
    await navigator.clipboard.writeText(account.email)
    setCopied(true)
    toast.success('Copiado al portapapeles')
    setTimeout(() => setCopied(false), 2000)
  }

  // ─── Reset ─────────────────────────────────────────────────────

  const resetAll = () => {
    setAccount(null)
    setMessages([])
    setSelectedMsg(null)
    setFullMsg(null)
    setAutoRefresh(false)
    if (refreshTimeoutRef.current) clearTimeout(refreshTimeoutRef.current)
    refreshTimeoutRef.current = null
    fetch('/api/tempmail/account', { method: 'DELETE' }).catch(() => {})
  }

  // ─── Render ────────────────────────────────────────────────────

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!allowed) return null

  const cfg = serviceConfig[selectedService]

  return (
    <div className="space-y-6 matrix-bg min-h-screen rounded-xl border border-red-900/30 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-red-500/20 pb-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Mail className="h-10 w-10 text-red-500 animate-pulse-glow" />
            <h1 className="text-4xl font-black uppercase tracking-widest text-white neon-text-red">
              TEMP MAIL
            </h1>
          </div>
          <p className="mt-2 font-mono-cyber text-sm text-red-500/80 uppercase">
            &gt; Correo temporal con selección de dominio
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">RANGO:</span>
          <span className="font-mono-cyber text-xs font-bold text-red-400 border border-red-500/30 bg-red-950/30 px-2 py-0.5">
            {rank?.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Service selector */}
      <div className="space-y-2">
        <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">SELECCIONAR SERVICIO</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {(Object.keys(serviceConfig) as Service[]).map((svc) => {
            const c = serviceConfig[svc]
            const active = selectedService === svc
            return (
              <button
                key={svc}
                onClick={() => { setSelectedService(svc); resetAll() }}
                className={`flex flex-col gap-1 px-4 py-3 text-left transition-all duration-300 border cursor-pointer ${
                  active
                    ? `${c.border} bg-gradient-to-br from-red-950/50 to-black shadow-[0_0_20px_rgba(239,68,68,0.15)]`
                    : 'border-gray-800 bg-black/60 hover:border-red-900/50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Globe className={`h-4 w-4 ${active ? c.color : 'text-gray-600'}`} />
                  <span className={`font-mono-cyber text-sm font-bold ${active ? c.color : 'text-gray-500'}`}>
                    {c.name}
                  </span>
                  {active && (
                    <span className={`ml-auto text-[10px] font-mono-cyber uppercase px-1.5 py-0.5 border ${c.badge}`}>
                      Activo
                    </span>
                  )}
                </div>
                <p className="font-mono-cyber text-[10px] text-gray-600 leading-relaxed">{c.desc}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Domain selector + Generate */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
        {(selectedService === 'mailtm' || selectedService === 'guerrillamail') && (
          <div className="flex-1 w-full sm:w-auto space-y-1">
            <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500">DOMINIO</p>
            <div className="flex items-center gap-2">
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                disabled={loadingDomains || !!account}
                className="w-full sm:w-64 bg-black border border-gray-700 text-gray-300 font-mono-cyber text-xs px-3 py-2.5 focus:outline-none focus:border-red-500/50 disabled:opacity-50"
              >
                {loadingDomains ? (
                  <option>Cargando dominios...</option>
                ) : domains.length === 0 ? (
                  <option>No hay dominios disponibles</option>
                ) : (
                  domains.map((d) => (
                    <option key={d.domain} value={d.domain}>
                      @{d.domain} {d.isActive ? '' : '(inactivo)'}
                    </option>
                  ))
                )}
              </select>
              <button
                onClick={() => loadDomains(selectedService)}
                disabled={loadingDomains || !!account}
                className="border border-gray-700 bg-black/50 px-3 py-2.5 text-gray-400 hover:text-red-400 transition-colors cursor-pointer disabled:opacity-50"
                title="Refrescar dominios"
              >
                <RefreshCw className={`h-4 w-4 ${loadingDomains ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        )}

        <button
          onClick={generateEmail}
          disabled={generating || (!selectedDomain && selectedService === 'mailtm')}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-mono-cyber text-sm font-bold uppercase px-6 py-2.5 transition-all duration-200 shadow-[0_0_15px_rgba(239,68,68,0.4)] hover:shadow-[0_0_25px_rgba(239,68,68,0.6)] cursor-pointer"
        >
          {generating ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Zap className="h-4 w-4" />
          )}
          {generating ? 'GENERANDO...' : `GENERAR`}
        </button>

        {account && (
          <button
            onClick={resetAll}
            className="flex items-center gap-2 border border-gray-700 bg-black/50 hover:border-red-900/50 text-gray-500 hover:text-red-400 font-mono-cyber text-xs uppercase px-4 py-2.5 transition-all duration-200 cursor-pointer"
          >
            <Trash2 className="h-3 w-3" />
            Limpiar
          </button>
        )}
      </div>

      {/* Email display + inbox */}
      {account && (
        <div className="space-y-4">
          {/* Email card */}
          <div className={`border ${cfg.border} bg-black/80 p-4 relative overflow-hidden`}>
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-500/60 to-transparent" />
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex-1 min-w-0">
                <p className="font-mono-cyber text-[10px] uppercase tracking-widest text-gray-500 mb-1">
                  TU CORREO TEMPORAL
                </p>
                <p className={`font-mono-cyber text-lg font-black ${cfg.color} truncate`}>
                  {account.email}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-[10px] font-mono-cyber uppercase px-2 py-0.5 border ${cfg.badge}`}>
                  {serviceConfig[account.service].name}
                </span>
                <button
                  onClick={copyEmail}
                  className="flex items-center gap-1.5 border border-gray-700 hover:border-red-500/50 bg-black/50 px-3 py-1.5 text-xs font-mono-cyber text-gray-400 hover:text-white transition-all duration-200 cursor-pointer"
                >
                  {copied ? (
                    <CheckCircle2 className="h-3 w-3 text-green-400" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  {copied ? 'COPIADO' : 'COPIAR'}
                </button>
                <button
                  onClick={() => fetchInbox(account)}
                  disabled={refreshing}
                  className="flex items-center gap-1.5 border border-red-900/40 hover:border-red-500/50 bg-red-950/20 px-3 py-1.5 text-xs font-mono-cyber text-red-400 hover:text-red-300 transition-all duration-200 cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                  ACTUALIZAR
                </button>
              </div>
            </div>

            {/* Auto-refresh */}
            <div className="mt-3 pt-3 border-t border-gray-800 flex items-center gap-3">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center gap-2 text-[10px] font-mono-cyber uppercase transition-colors cursor-pointer ${
                  autoRefresh ? 'text-green-400' : 'text-gray-600 hover:text-gray-400'
                }`}
              >
                <div className={`w-7 h-3.5 rounded-full relative transition-colors duration-300 ${autoRefresh ? 'bg-green-600' : 'bg-gray-800'}`}>
                  <div className={`absolute top-0.5 h-2.5 w-2.5 rounded-full bg-white transition-all duration-300 ${autoRefresh ? 'left-3.5' : 'left-0.5'}`} />
                </div>
                Auto-refresh (8s)
              </button>
              {autoRefresh && (
                <span className="flex items-center gap-1 text-[10px] font-mono-cyber text-green-400">
                  <Clock className="h-3 w-3 animate-pulse" />
                  Actualizando automáticamente...
                </span>
              )}
            </div>
          </div>

          {/* Inbox + Reader side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Messages */}
            <div className="border border-gray-800 bg-black/60 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#0a0a0f]">
                <div className="flex items-center gap-2">
                  <Inbox className="h-4 w-4 text-red-400" />
                  <span className="font-mono-cyber text-xs font-bold uppercase text-red-400">Bandeja de Entrada</span>
                </div>
                <span className="font-mono-cyber text-[10px] text-gray-500">
                  {messages.length} {messages.length === 1 ? 'mensaje' : 'mensajes'}
                </span>
              </div>

              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                  <Terminal className="h-12 w-12 text-gray-800 mb-3" />
                  <p className="font-mono-cyber text-xs text-gray-600 uppercase">Bandeja vacía</p>
                  <p className="font-mono-cyber text-[10px] text-gray-700 mt-1">
                    Esperando correos entrantes...
                  </p>
                  <button
                    onClick={() => fetchInbox(account)}
                    disabled={refreshing}
                    className="mt-4 flex items-center gap-1.5 border border-red-900/30 bg-red-950/10 px-4 py-2 text-[10px] font-mono-cyber text-red-400/70 hover:text-red-400 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                    Verificar correos
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-gray-800/60 max-h-[450px] overflow-y-auto">
                  {messages.map((msg) => (
                    <button
                      key={msg.id}
                      onClick={() => readMessage(msg)}
                      className={`w-full text-left px-4 py-3 hover:bg-red-950/10 transition-all duration-200 cursor-pointer group flex items-start gap-3 ${
                        selectedMsg?.id === msg.id ? 'bg-red-950/20 border-l-2 border-red-500' : 'border-l-2 border-transparent'
                      }`}
                    >
                      <div className={`mt-1 h-2 w-2 rounded-full shrink-0 ${msg.seen === false ? 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.8)]' : 'bg-gray-700'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-mono-cyber text-xs text-white truncate">
                            {fromAddress(msg.from)}
                          </p>
                          <span className="font-mono-cyber text-[10px] text-gray-600 shrink-0 flex items-center gap-0.5">
                            <Clock className="h-2.5 w-2.5" />
                            {timeAgo(msg.createdAt || msg.date)}
                          </span>
                        </div>
                        <p className="font-mono-cyber text-[11px] text-gray-400 truncate mt-0.5">
                          {msg.subject || '(Sin asunto)'}
                        </p>
                        {msg.intro && (
                          <p className="font-mono-cyber text-[10px] text-gray-600 truncate mt-0.5">
                            {msg.intro}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="h-3 w-3 text-gray-700 group-hover:text-red-400 shrink-0 mt-1 transition-colors" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Message reader */}
            <div className="border border-gray-800 bg-black/60 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-[#0a0a0f]">
                <Eye className="h-4 w-4 text-red-400" />
                <span className="font-mono-cyber text-xs font-bold uppercase text-red-400">Lector de Correo</span>
              </div>

              {!selectedMsg ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                  <Mail className="h-12 w-12 text-gray-800 mb-3" />
                  <p className="font-mono-cyber text-xs text-gray-600 uppercase">Selecciona un mensaje</p>
                  <p className="font-mono-cyber text-[10px] text-gray-700 mt-1">
                    Haz clic en un correo para leerlo
                  </p>
                </div>
              ) : loadingMsg ? (
                <div className="flex items-center justify-center py-16">
                  <RefreshCw className="h-6 w-6 text-red-500 animate-spin" />
                </div>
              ) : fullMsg ? (
                <div className="p-4 space-y-3 max-h-[450px] overflow-y-auto">
                  <button
                    onClick={() => { setSelectedMsg(null); setFullMsg(null) }}
                    className="flex items-center gap-1.5 text-[10px] font-mono-cyber text-gray-500 hover:text-red-400 transition-colors cursor-pointer mb-2"
                  >
                    <ArrowLeft className="h-3 w-3" />
                    Volver
                  </button>

                  <div className="space-y-1.5 border border-gray-800 bg-black/40 p-3">
                    <div className="grid grid-cols-[60px_1fr] gap-1 text-[11px] font-mono-cyber">
                      <span className="text-gray-600 uppercase">De:</span>
                      <span className="text-gray-300 truncate">{fromAddress(fullMsg.from)}</span>
                    </div>
                    <div className="grid grid-cols-[60px_1fr] gap-1 text-[11px] font-mono-cyber">
                      <span className="text-gray-600 uppercase">Asunto:</span>
                      <span className="text-white">{fullMsg.subject || '(Sin asunto)'}</span>
                    </div>
                    {(fullMsg.createdAt || fullMsg.date) && (
                      <div className="grid grid-cols-[60px_1fr] gap-1 text-[11px] font-mono-cyber">
                        <span className="text-gray-600 uppercase">Fecha:</span>
                        <span className="text-gray-400">{formatDate(fullMsg.createdAt || fullMsg.date)}</span>
                      </div>
                    )}
                  </div>

                  {(fullMsg.html && fullMsg.html.length > 0) ? (
                    <div className="border border-gray-800 bg-white/5 overflow-hidden">
                      <div className="px-3 py-1.5 border-b border-gray-800 bg-black/40">
                        <span className="font-mono-cyber text-[10px] text-green-400 uppercase">HTML</span>
                      </div>
                      <iframe
                        srcDoc={Array.isArray(fullMsg.html) ? fullMsg.html.join('') : fullMsg.html as string}
                        className="w-full min-h-[200px] bg-white"
                        sandbox="allow-same-origin"
                        title="Contenido del correo"
                      />
                    </div>
                  ) : fullMsg.textBody ? (
                    <div className="border border-gray-800 bg-black/40 p-3">
                      <p className="font-mono-cyber text-[10px] text-gray-400 uppercase mb-2 flex items-center gap-1">
                        <Terminal className="h-3 w-3" />
                        Texto plano
                      </p>
                      <pre className="font-mono-cyber text-xs text-gray-300 whitespace-pre-wrap break-words">
                        {fullMsg.textBody}
                      </pre>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 border border-yellow-900/30 bg-yellow-950/10 px-3 py-2">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      <p className="font-mono-cyber text-[11px] text-yellow-400">Sin contenido legible</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Info cards */}
      {!account && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          {(Object.entries(serviceConfig) as [Service, typeof serviceConfig[Service]][]).map(([svc, c]) => (
            <div key={svc} className={`border ${c.border} bg-black/50 p-4`}>
              <div className="flex items-center gap-2 mb-2">
                <Globe className={`h-4 w-4 ${c.color}`} />
                <span className={`font-mono-cyber text-sm font-bold ${c.color}`}>{c.name}</span>
              </div>
              <p className="font-mono-cyber text-[11px] text-gray-500 leading-relaxed">{c.desc}</p>
              <div className="mt-3 flex flex-col gap-1">
                {{
                  mailtm: ['Genera cuenta automática', 'API REST moderna', 'Múltiples dominios'],
                  guerrillamail: ['Sin registro', '7 dominios para elegir', 'Dura ~1 hora'],
                  tempmail_lol: ['Sin registro', 'Cuerpo completo en inbox', 'Gratis sin API key'],
                  dropmail: ['GraphQL', 'Hasta 30 días', 'Dominios dinámicos'],
                }[svc]!.map((feat) => (
                  <div key={feat} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3 w-3 text-green-500/70 shrink-0" />
                    <span className="font-mono-cyber text-[10px] text-gray-600">{feat}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
