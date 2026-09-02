'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import { toast } from '@/lib/toast'
import {
  Play, Square, Sparkles, Activity, CheckCircle2, XCircle,
  Zap, Terminal, X, Globe, AlertTriangle, Cpu, Copy, Trash2,
  Settings, ChevronLeft, ChevronRight, ShoppingBag
} from 'lucide-react'
import { useSound } from '@/hooks/use-sound'

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
  apiUrl: string
  stats: GateStats
}

interface CardResult {
  card: string
  status: 'live' | 'dead' | 'error'
  response?: string
  time_taken?: number
}

interface ShopifyVariant {
  id: number
  title: string
  price: string
}

interface ShopifyProduct {
  id: number
  title: string
  handle: string
  image: string | null
  variants: ShopifyVariant[]
}

interface ShopifyConfig {
  url: string
  sendAddress: boolean
  addrStreet: string
  addrCity: string
  addrState: string
  addrZip: string
  addrPhone: string
  addrEmail: string
  product: {
    id: number
    title: string
    handle: string
    image: string | null
    variant: { id: number; title: string; price: string }
  } | null
}

function luhnGenerate(bin: string, length: number = 16): string {
  const n = length - bin.length - 1
  if (n < 0) return bin
  let partial = bin
  for (let i = 0; i < n; i++) {
    partial += Math.floor(Math.random() * 10).toString()
  }
  const digits = partial.split('').map(Number)
  let sum = 0
  let alt = true
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits[i]
    if (alt) d *= 2
    if (d > 9) d -= 9
    sum += d
    alt = !alt
  }
  const check = (10 - (sum % 10)) % 10
  return partial + check
}

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 11 }, (_, i) => String(currentYear + i).slice(2))
const monthOptions = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))

export default function GatePage() {
  const params = useParams()
  const [gate, setGate] = useState<Gate | null>(null)
  const [loading, setLoading] = useState(true)
  const [cards, setCards] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [userCredits, setUserCredits] = useState(0)
  const [showGenModal, setShowGenModal] = useState(false)
  const [genData, setGenData] = useState({ bin: '', month: '', year: '', cvv: '', quantity: '10' })
  const [shopifyConfig, setShopifyConfig] = useState<ShopifyConfig | null>(null)
  const [showShopifyModal, setShowShopifyModal] = useState(false)
  const [siteUrlInput, setSiteUrlInput] = useState('')
  const [shopifyProducts, setShopifyProducts] = useState<ShopifyProduct[]>([])
  const [shopifyPage, setShopifyPage] = useState(1)
  const [shopifyLoading, setShopifyLoading] = useState(false)
  const [shopifyError, setShopifyError] = useState('')
  const [shopifyVerified, setShopifyVerified] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<ShopifyProduct | null>(null)
  const [modalSendAddr, setModalSendAddr] = useState(false)
  const [modalAddrStreet, setModalAddrStreet] = useState('')
  const [modalAddrCity, setModalAddrCity] = useState('')
  const [modalAddrState, setModalAddrState] = useState('')
  const [modalAddrZip, setModalAddrZip] = useState('')
  const [modalAddrPhone, setModalAddrPhone] = useState('')
  const [modalAddrEmail, setModalAddrEmail] = useState('')
  const [shopifySearch, setShopifySearch] = useState('')
  const [threadCount, setThreadCount] = useState(1)
  const [liveResults, setLiveResults] = useState<CardResult[]>([])
  const [deadResults, setDeadResults] = useState<CardResult[]>([])
  const [processedCount, setProcessedCount] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [insufficientCredits, setInsufficientCredits] = useState(false)
  const [showCreditWarning, setShowCreditWarning] = useState(false)
  const [creditWarningData, setCreditWarningData] = useState({ current: 0, worstCase: 0 })
  const creditWarningResolve = useRef<((value: boolean) => void) | null>(null)
  const stopRef = useRef(false)
  const liveRef = useRef<HTMLDivElement>(null)
  const deadRef = useRef<HTMLDivElement>(null)
  const playSound = useSound()

  useEffect(() => {
    async function fetchGate() {
      try {
        const [gateRes, creditsRes] = await Promise.all([
          fetch(`/api/gates/${params.id}`),
          fetch('/api/user/credits'),
        ])
        const gateData = await gateRes.json()
        setGate(gateData)
        if (creditsRes.ok) {
          const creditsData = await creditsRes.json()
          if (creditsData.credits !== undefined) {
            setUserCredits(creditsData.credits)
            window.dispatchEvent(new CustomEvent('credits-updated', { detail: creditsData.credits }))
          }
        }
      } catch (error) {
        console.error('Error fetching gate:', error)
      }
      setLoading(false)
    }
    if (params.id) fetchGate()
  }, [params.id])

  const handleStart = async () => {
    const lines = cards.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length || !gate) return

    const currentCredits = userCredits

    const minCost = Math.min(gate.creditsLive, gate.creditsDead)
    const maxCostPerCard = Math.max(gate.creditsLive, gate.creditsDead)
    const worstCaseCost = lines.length * maxCostPerCard

    if (currentCredits < minCost) {
      setInsufficientCredits(true)
      return
    }

    if (currentCredits < worstCaseCost) {
      setCreditWarningData({ current: currentCredits, worstCase: worstCaseCost })
      setShowCreditWarning(true)
      const proceed = await new Promise<boolean>((resolve) => {
        creditWarningResolve.current = resolve
      })
      setShowCreditWarning(false)
      if (!proceed) return
    }

    stopRef.current = false
    setIsRunning(true)
    setInsufficientCredits(false)
    setLiveResults([])
    setDeadResults([])
    setProcessedCount(0)
    setTotalCount(lines.length)
    playSound('start')
    toast(`Procesando ${lines.length} tarjeta(s)...`, {
      icon: '⚡', duration: 3000,
      style: { background: '#111', border: '1px solid #f59e0b', color: '#fbbf24' }
    })

    const processedSet = new Set<string>()
    let localLives = 0
    let localDeads = 0
    let currentIndex = 0

    const processCard = async (card: string, index: number): Promise<void> => {
      if (stopRef.current) return
      try {
        const res = await fetch(`/api/gates/${gate.id}/check`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            card,
            website: shopifyConfig?.url || '',
            email: shopifyConfig?.sendAddress ? shopifyConfig.addrEmail : '',
            address: shopifyConfig?.sendAddress
              ? {
                street: shopifyConfig.addrStreet,
                city: shopifyConfig.addrCity,
                state: shopifyConfig.addrState,
                zip: shopifyConfig.addrZip,
                phone: shopifyConfig.addrPhone,
              }
              : false,
            product: shopifyConfig?.product ? {
              id: shopifyConfig.product.id,
              handle: shopifyConfig.product.handle,
              title: shopifyConfig.product.title,
              variant: shopifyConfig.product.variant,
            } : false,
          }),
        })
        const data = await res.json()
        if (data.creditsRemaining !== undefined) {
          setUserCredits(data.creditsRemaining)
          window.dispatchEvent(new CustomEvent('credits-updated', { detail: data.creditsRemaining }))
        }

        if (data.error?.toLowerCase?.().includes('baneado')) {
          setIsRunning(false)
          setInsufficientCredits(false)
          toast.error('Has sido baneado del sistema', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #a855f7', color: '#c084fc' }
          })
          stopRef.current = true
          return
        }
        if (data.error?.toLowerCase?.().includes('membresía expirada')) {
          setIsRunning(false)
          setInsufficientCredits(false)
          toast.error('Membresía expirada — renueva para usar los gates', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #eab308', color: '#facc15' }
          })
          stopRef.current = true
          return
        }

        if (data.error?.toLowerCase?.().includes('rango insuficiente')) {
          setIsRunning(false)
          setInsufficientCredits(false)
          toast.error('Rango insuficiente para acceder a este gate', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #a855f7', color: '#c084fc' }
          })
          stopRef.current = true
          return
        }

        if (data.status === 'error' && data.error?.toLowerCase?.().includes('creditos insuficientes')) {
          setInsufficientCredits(true)
          setIsRunning(false)
          toast.error('Créditos insuficientes — procesamiento detenido', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #a855f7', color: '#c084fc' }
          })
          stopRef.current = true
          return
        }

        if (data.error?.toLowerCase?.().includes('deshabilitado')) {
          setIsRunning(false)
          setInsufficientCredits(false)
          toast.error('Gate deshabilitado — solo administradores pueden procesar', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #a855f7', color: '#c084fc' }
          })
          stopRef.current = true
          return
        }

        if (data.code === 'NO_API_URL') {
          setIsRunning(false)
          setInsufficientCredits(false)
          toast.warning('Gate en desarrollo — no se puede procesar', {
            duration: 4000,
            style: { background: '#111', border: '1px solid #eab308', color: '#facc15' }
          })
          stopRef.current = true
          return
        }

        const result: CardResult = { card, status: data.status ?? 'error', response: data.response ?? 'Error in API', time_taken: data.time_taken }
        if (data.status === 'live') {
          localLives++
          setLiveResults(prev => [...prev, result])
          setTimeout(() => liveRef.current?.scrollTo({ top: liveRef.current.scrollHeight, behavior: 'smooth' }), 50)
        } else {
          localDeads++
          setDeadResults(prev => [...prev, result])
          setTimeout(() => deadRef.current?.scrollTo({ top: deadRef.current.scrollHeight, behavior: 'smooth' }), 50)
        }
      } catch {
        localDeads++
        setDeadResults(prev => [...prev, { card, status: 'error' }])
      }
      processedSet.add(card)
      setCards(lines.filter(l => !processedSet.has(l)).join('\n'))
      setProcessedCount(prev => prev + 1)
    }

    while (currentIndex < lines.length && !stopRef.current) {
      // Launch threadCount promises
      const batch: Promise<void>[] = []
      for (let t = 0; t < threadCount && currentIndex < lines.length && !stopRef.current; t++) {
        const idx = currentIndex++
        const card = lines[idx]
        batch.push(processCard(card, idx))
      }
      await Promise.all(batch)
      if (currentIndex < lines.length && !stopRef.current) {
        await new Promise(r => setTimeout(r, 200))
      }
    }
    setIsRunning(false)
    if (stopRef.current) {
      toast.info('Procesamiento detenido', {
        icon: '⏹️', duration: 3000,
        style: { background: '#111', border: '1px solid #f97316', color: '#fb923c' }
      })
    } else {
      playSound('done')
      toast.success(`Proceso finalizado exitosamente`, {
        icon: '✅', duration: 5000,
        style: { background: '#111', border: '1px solid #22c55e', color: '#4ade80' }
      })
    }
  }

  const handleStop = () => { stopRef.current = true; setIsRunning(false) }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch { }
  }

  const removeLive = (index: number) => {
    setLiveResults(prev => prev.filter((_, i) => i !== index))
  }

  const removeDead = (index: number) => {
    setDeadResults(prev => prev.filter((_, i) => i !== index))
  }

  const copyAllLive = () => {
    const text = liveResults.map(r => r.card).join('\n')
    if (text) navigator.clipboard.writeText(text)
  }

  const removeAllLive = () => setLiveResults([])

  const copyAllDead = () => {
    const text = deadResults.map(r => r.card).join('\n')
    if (text) navigator.clipboard.writeText(text)
  }

  const removeAllDead = () => setDeadResults([])

  const handleExecuteGen = () => {
    const { bin, month, year, cvv, quantity } = genData

    if (!bin.length || bin.length < 6 || bin.length > 16) {
      toast.error('Ingresa un BIN válido', {
        icon: '❌', duration: 3000,
        style: { background: '#111', border: '1px solid #a855f7', color: '#c084fc' }
      })
      return
    }

    const count = Math.min(Math.max(parseInt(quantity) || 10, 1), 100)
    const generated: string[] = []
    for (let i = 0; i < count; i++) {
      let m = month
      if (!m) m = String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')
      let y = year
      if (!y) y = String(currentYear + Math.floor(Math.random() * 11)).slice(2)
      let c = cvv
      if (!c) c = String(Math.floor(Math.random() * 900) + 100)
      const b = bin || '4'
      const fullPan = luhnGenerate(b.replace(/\s/g, ''))
      generated.push(`${fullPan}|${m}|${y}|${c}`)
    }
    setCards(generated.join('\n'))
    setShowGenModal(false)
  }

  const handleVerifySite = async () => {
    if (!siteUrlInput.trim()) {
      setShopifyError('Ingresa una URL válida')
      return
    }
    let baseUrl: string
    try {
      baseUrl = new URL(siteUrlInput.trim()).origin
    } catch {
      setShopifyError('URL inválida. Debe ser como https://shopify_site.com')
      return
    }
    setShopifyLoading(true)
    setShopifyError('')
    try {
      const url = `/api/gates/shopify-products?url=${encodeURIComponent(baseUrl)}`
      const res = await fetch(url)
      const data = await res.json()
      if (data.error) {
        setShopifyError(data.error)
        setShopifyProducts([])
      } else {
        setShopifyProducts(data.products)
        setShopifyPage(1)
        setShopifyVerified(true)
        setSelectedProduct(null)
      }
    } catch {
      setShopifyError('Error de conexión al verificar el sitio')
    }
    setShopifyLoading(false)
  }

  const filteredProducts = shopifyProducts.filter(p =>
    !shopifySearch.trim() || p.title.toLowerCase().includes(shopifySearch.toLowerCase())
  )
  const PRODUCTS_PER_PAGE = 5
  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / PRODUCTS_PER_PAGE))
  const pagedProducts = filteredProducts.slice((shopifyPage - 1) * PRODUCTS_PER_PAGE, shopifyPage * PRODUCTS_PER_PAGE)

  const handleLoadShopifyPage = (page: number) => {
    setShopifyPage(page)
  }

  if (loading) return <div className="matrix-bg rounded-xl min-h-[500px]" />

  if (!gate) {
    return (
      <div className="flex flex-col items-center justify-center border border-dashed border-purple-500/30 bg-purple-950/10 py-20 cyber-clip min-h-[500px] matrix-bg">
        <Terminal className="h-16 w-16 text-purple-500/50 mb-4" />
        <h3 className="font-mono-cyber text-lg font-bold text-purple-500 uppercase tracking-widest neon-text-purple">ERROR: GATE NO ENCONTRADO</h3>
        <p className="mt-2 font-mono-cyber text-sm text-purple-400/70">&gt; El gate solicitado no existe o el acceso denegado.</p>
      </div>
    )
  }

  const progress = totalCount > 0 ? Math.round((processedCount / totalCount) * 100) : 0

  return (
    <div className="space-y-6 p-6 matrix-bg min-h-screen rounded-xl border border-purple-900/30">

      {/* ── Header Banner ── */}
      <div className="relative overflow-hidden cyber-clip border border-purple-500/50 bg-black/80">
        <div className="absolute inset-0 bg-[url('/images/gate-banner.jpg')] bg-cover bg-center opacity-30 mix-blend-luminosity" />
        <div className="absolute inset-0 bg-gradient-to-r from-black via-purple-950/40 to-black/90" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(168,85,247,0.1)_50%)] bg-[length:100%_4px] animate-scan-line" />

        <div className="relative flex flex-col md:flex-row md:items-center justify-between p-8 z-10 gap-6">
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            <div className="relative h-32 w-48 cyber-clip border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
              <Image src="/images/gate-banner.jpg" alt="Gate Banner" fill className="object-cover mix-blend-screen filter grayscale opacity-70" />
              <div className="absolute inset-0 bg-purple-500/20 mix-blend-overlay" />
            </div>
            <div>
              <h1 className="text-4xl font-black uppercase tracking-widest text-white neon-text-purple">{gate.name}</h1>
              <p className="mt-1 font-mono-cyber text-xs text-purple-400/60">ID: {gate.id}</p>
              <span className="mt-3 inline-block cyber-clip-alt bg-purple-500/20 border border-purple-500/50 px-4 py-1.5 text-xs font-mono-cyber font-bold uppercase text-purple-400">
                &lt;{gate.category}&gt;
              </span>
              <div className="mt-3">
                <p className="mb-1.5 font-mono-cyber text-[10px] font-bold uppercase tracking-widest text-gray-500">GLOBAL STATS</p>
                <div className="flex flex-wrap items-center gap-2 font-mono-cyber text-[10px]">
                  <span className="flex items-center gap-1 border border-green-500/30 bg-green-950/40 px-2 py-1 rounded text-green-400 whitespace-nowrap">
                    <CheckCircle2 className="h-3 w-3 shrink-0" /><span className="font-bold">{gate.stats.lives}</span> <span className="text-green-500">LIVES</span>
                  </span>
                  <span className="flex items-center gap-1 border border-purple-500/30 bg-purple-950/40 px-2 py-1 rounded text-purple-400 whitespace-nowrap">
                    <XCircle className="h-3 w-3 shrink-0" /><span className="font-bold">{gate.stats.deads}</span> <span className="text-purple-500">DEADS</span>
                  </span>
                  <span className="flex items-center gap-1 border border-gray-600 bg-gray-800/60 px-2 py-1 rounded text-gray-400 whitespace-nowrap">
                    <Activity className="h-3 w-3 shrink-0" /><span className="font-bold">{gate.stats.total}</span> <span className="text-gray-500">TOTAL</span>
                  </span>
                  <span className={`flex items-center gap-1 px-2 py-1 rounded whitespace-nowrap ${gate.stats.successRate >= 50
                    ? 'border border-green-500/30 bg-green-950/40 text-green-400'
                    : gate.stats.successRate > 0
                      ? 'border border-yellow-500/30 bg-yellow-950/40 text-yellow-400'
                      : 'border border-gray-600 bg-gray-800/60 text-gray-400'
                    }`}>
                    <span className="font-bold">{gate.stats.successRate}%</span> <span className="opacity-70">RATE</span>
                  </span>
                  <span className={`flex items-center gap-1 px-2 py-1 rounded whitespace-nowrap border ${gate.minRank === 'admin' ? 'text-purple-400 border-purple-500/30 bg-purple-950/30' :
                    gate.minRank === 'moderador' ? 'text-purple-400 border-purple-500/30 bg-purple-950/30' :
                      gate.minRank === 'seller' ? 'text-blue-400 border-blue-500/30 bg-blue-950/30' :
                        gate.minRank === 'vip' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-950/30' :
                          'text-green-400 border-green-500/30 bg-green-950/30'
                    }`}>
                    <span className="font-bold uppercase">{gate.minRank}</span> <span className="opacity-70">RANK/min</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 cyber-clip-alt border border-purple-500/50 bg-black/80 px-6 py-4 backdrop-blur-md shadow-[0_0_15px_rgba(168,85,247,0.2)]">
            <div>
              <p className="font-bold text-white uppercase tracking-wider text-sm">Information</p>
              <p className="flex items-center gap-1 font-mono-cyber text-sm font-bold text-purple-400 mt-1">
                <Zap className="h-3 w-3" />{userCredits}
              </p>
              <div className="mt-2 flex items-center gap-2 font-mono-cyber text-[10px]">
                <span className="flex items-center gap-1.5 text-green-400 border border-green-500/30 bg-green-950/40 px-2 py-1">
                  <Zap className="h-3 w-3" />{gate.creditsLive} <span className="text-green-600">/ LIVE</span>
                </span>
                <span className="flex items-center gap-1.5 text-purple-400 border border-purple-500/30 bg-purple-950/40 px-2 py-1">
                  <Zap className="h-3 w-3" />{gate.creditsDead} <span className="text-purple-700">/ DEAD</span>
                </span>
              </div>
              <div className="mt-2 font-mono-cyber text-[10px]">
                <label className="block text-cyan-400 uppercase tracking-wider mb-1">Threads</label>
                <select
                  value={threadCount}
                  onChange={(e) => setThreadCount(Number(e.target.value))}
                  className="border border-cyan-900/50 bg-black/50 px-2 py-1 text-cyan-400 focus:border-cyan-500 focus:outline-none cursor-pointer text-[10px]">
                  {Array.from({ length: gate.threads ?? 1 }, (_, i) => i + 1).map(t => (
                    <option key={t} value={t} className="bg-black text-cyan-400">{t} thread{t > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {/* Live */}
        <div className="relative overflow-hidden cyber-clip border border-green-500/30 bg-black/80 p-4">
          <div className="flex flex-col items-center">
            <div className="mb-2 cyber-clip-alt border border-green-500/30 bg-green-950/40 p-2"><CheckCircle2 className="h-5 w-5 text-green-400" /></div>
            <span className="font-mono-cyber text-3xl font-black text-green-400">{liveResults.length}</span>
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-green-700 mt-1">LIVE</span>
          </div>
        </div>

        {/* Dead */}
        <div className="relative overflow-hidden cyber-clip border border-purple-500/30 bg-black/80 p-4">
          <div className="flex flex-col items-center">
            <div className="mb-2 cyber-clip-alt border border-purple-500/30 bg-purple-950/40 p-2"><XCircle className="h-5 w-5 text-purple-500" /></div>
            <span className="font-mono-cyber text-3xl font-black text-purple-500">{deadResults.length}</span>
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-purple-700 mt-1">DEAD</span>
          </div>
        </div>

        {/* Total */}
        <div className="relative overflow-hidden cyber-clip border border-blue-500/30 bg-black/80 p-4">
          <div className="flex flex-col items-center">
            <div className="mb-2 cyber-clip-alt border border-blue-500/30 bg-blue-950/40 p-2"><Activity className="h-5 w-5 text-blue-400" /></div>
            <span className="font-mono-cyber text-3xl font-black text-blue-400">{totalCount}</span>
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-blue-700 mt-1">TOTAL</span>
          </div>
        </div>

        {/* Faltantes */}
        <div className="relative overflow-hidden cyber-clip border border-yellow-500/30 bg-black/80 p-4">
          <div className="flex flex-col items-center">
            <div className="mb-2 cyber-clip-alt border border-yellow-500/30 bg-yellow-950/40 p-2"><Cpu className="h-5 w-5 text-yellow-400" /></div>
            <span className="font-mono-cyber text-3xl font-black text-yellow-400">{Math.max(0, totalCount - processedCount)}</span>
            <span className="font-mono-cyber text-[10px] uppercase tracking-widest text-yellow-700 mt-1">FALTANTES</span>
          </div>
        </div>
      </div>

      {/* ── Input + Shopify URL ── */}
      <div className="space-y-4">
        <div className="relative overflow-hidden cyber-clip border border-purple-500/50 bg-black/90 p-4 shadow-[inset_0_0_20px_rgba(168,85,247,0.1)]">
          <label className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-purple-400">
            <Terminal className="h-3 w-3" /> ENTRADA DE DATOS
          </label>
          <textarea
            value={cards}
            onChange={(e) => setCards(e.target.value)}
            placeholder="> Ingresa las tarjetas aquí... (una por línea: número|mm|yy|cvv)"
            className="h-24 w-full resize-none bg-black/50 px-3 py-2 font-mono-cyber text-sm text-purple-400 placeholder-purple-900/50 focus:border-purple-400 focus:outline-none border border-purple-900/50"
          />
        </div>

        {gate.category === 'shopify' && (
          <div className="relative overflow-hidden cyber-clip border border-orange-500/50 bg-black/90 p-4 shadow-[inset_0_0_20px_rgba(249,115,22,0.1)]">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-orange-400">
                <Globe className="h-3 w-3" /> SITIO WEB
              </label>
              <button onClick={() => {
                setSiteUrlInput(shopifyConfig?.url || '')
                setShopifyProducts([])
                setShopifyPage(1)
                setShopifyLoading(false)
                setShopifyError('')
                setShopifyVerified(false)
                setSelectedProduct(shopifyConfig?.product ? {
                  id: shopifyConfig.product.id,
                  title: shopifyConfig.product.title,
                  handle: shopifyConfig.product.handle,
                  image: shopifyConfig.product.image,
                  variants: [shopifyConfig.product.variant],
                } : null)
                setModalSendAddr(shopifyConfig?.sendAddress ?? false)
                setModalAddrStreet(shopifyConfig?.addrStreet || '')
                setModalAddrCity(shopifyConfig?.addrCity || '')
                setModalAddrState(shopifyConfig?.addrState || '')
                setModalAddrZip(shopifyConfig?.addrZip || '')
                setModalAddrPhone(shopifyConfig?.addrPhone || '')
                setModalAddrEmail(shopifyConfig?.addrEmail || '')
                setShopifySearch('')
                setShowShopifyModal(true)
              }}
                className="flex items-center gap-2 border border-orange-500/50 bg-orange-950/40 px-4 py-2 font-mono-cyber text-xs font-bold text-orange-400 transition-all hover:bg-orange-600 hover:text-white cursor-pointer">
                <Settings className="h-4 w-4" /> CONFIGURAR
              </button>
            </div>
            {shopifyConfig ? (
              <div className="mt-3 border border-orange-900/40 bg-orange-950/20 p-3 cyber-clip-alt space-y-2">
                <div className="flex flex-wrap items-center gap-3">
                  <Globe className="h-4 w-4 text-orange-400 shrink-0" />
                  <span className="font-mono-cyber text-xs text-orange-300 break-all">{shopifyConfig.url}</span>
                  {shopifyConfig.product && (
                    <>
                      <span className="text-orange-700">|</span>
                      <ShoppingBag className="h-4 w-4 text-orange-400 shrink-0" />
                      <span className="font-mono-cyber text-xs text-orange-300">{shopifyConfig.product.title}</span>
                      <span className="font-mono-cyber text-[10px] text-orange-600">({shopifyConfig.product.variant.title})</span>
                      <span className="font-mono-cyber text-xs text-green-400">${shopifyConfig.product.variant.price}</span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2 border-t border-orange-900/30 pt-2">
                  <span className={`font-mono-cyber text-[10px] px-2 py-0.5 border ${shopifyConfig.sendAddress ? 'border-blue-500/40 text-blue-400' : 'border-purple-500/40 text-purple-400'}`}>
                    {shopifyConfig.sendAddress ? 'ENVIAR DIRECCIÓN' : 'SIN DIRECCION'}
                  </span>
                  {shopifyConfig.sendAddress && (
                    <span className="font-mono-cyber text-[10px] text-blue-300 break-all">
                      {shopifyConfig.addrStreet}, {shopifyConfig.addrCity}, {shopifyConfig.addrState}, US — {shopifyConfig.addrPhone} — {shopifyConfig.addrEmail}
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <p className="mt-3 font-mono-cyber text-[10px] text-orange-700 italic">
                &gt; No hay sitio configurado. Presiona CONFIGURAR para agregar uno.
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── Action Buttons ── */}
      <div className="flex flex-col md:flex-row gap-4">
        <button onClick={handleStart} disabled={isRunning || insufficientCredits || !gate.apiUrl}
          className="group cyber-clip-alt flex flex-1 items-center justify-center gap-2 bg-purple-950/40 border border-purple-500/50 px-6 py-4 font-mono-cyber font-bold text-purple-400 transition-all hover:bg-purple-600 hover:text-white hover:shadow-[0_0_20px_rgba(168,85,247,0.6)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
          <Play className="h-5 w-5" /> INICIAR
        </button>
        <button onClick={handleStop} disabled={!isRunning}
          className="group cyber-clip-alt flex flex-1 items-center justify-center gap-2 border border-orange-500/50 bg-black/60 px-6 py-4 font-mono-cyber font-bold text-orange-500 transition-all hover:bg-orange-500 hover:text-black hover:shadow-[0_0_20px_rgba(249,115,22,0.6)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
          <Square className="h-5 w-5" /> DETENER
        </button>
        <button onClick={() => setShowGenModal(true)}
          className="group cyber-clip-alt flex flex-1 items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-orange-600 border border-purple-400 px-6 py-4 font-mono-cyber font-bold text-white transition-all hover:from-purple-500 hover:to-orange-500 hover:shadow-[0_0_25px_rgba(168,85,247,0.7)] cursor-pointer">
          <Sparkles className="h-5 w-5 animate-pulse" /> GENERAR TARJETAS
        </button>
      </div>

      {/* ── Gate deshabilitado Warning ── */}
      {!gate.isActive && (
        <div className="cyber-clip border border-purple-500/50 bg-purple-950/30 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-purple-500 shrink-0" />
            <p className="font-mono-cyber text-sm text-purple-400">
              GATE DESHABILITADO — Este gate está desactivado. Solo administradores pueden procesar tarjetas aquí.
            </p>
          </div>
        </div>
      )}

      {/* ── Gate en desarrollo Warning ── */}
      {!gate.apiUrl && (
        <div className="cyber-clip border border-yellow-500/50 bg-yellow-950/30 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500 shrink-0" />
            <p className="font-mono-cyber text-sm text-yellow-400">
              GATE EN DESARROLLO — Este gate aún no tiene una API configurada y no puede procesar tarjetas.
            </p>
          </div>
        </div>
      )}

      {/* ── Insufficient Credits Warning ── */}
      {insufficientCredits && (
        <div className="cyber-clip border border-purple-500/50 bg-purple-950/30 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-purple-500 shrink-0" />
            <p className="font-mono-cyber text-sm text-purple-400">
              CRÉDITOS INSUFICIENTES — Neitas al menos {Math.min(gate.creditsLive, gate.creditsDead)} crédito(s) para operar.
            </p>
          </div>
        </div>
      )}

      {/* ── Progress Bar ── */}
      {totalCount > 0 && (
        <div className="cyber-clip border border-purple-500/50 bg-black/90 p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-mono-cyber text-xs font-bold text-purple-400 uppercase tracking-widest">
              {isRunning ? 'PROCESANDO...' : 'COMPLETADO'}
            </span>
            <span className="font-mono-cyber text-sm font-black text-white">{processedCount}/{totalCount} — {progress}%</span>
          </div>
          <div className="h-2 w-full bg-gray-900 border border-purple-900/50 p-0.5">
            <div className="h-full bg-purple-500 transition-all duration-300 relative" style={{ width: `${progress}%` }}>
              {isRunning && <div className="absolute top-0 right-0 bottom-0 w-8 bg-white/50 animate-pulse" />}
            </div>
          </div>
          <div className="mt-2 flex gap-4 font-mono-cyber text-[10px]">
            <span className="text-green-400">✓ LIVE: {liveResults.length}</span>
            <span className="text-purple-500">✗ DEAD: {deadResults.length}</span>
            <span className="text-gray-600">CR: {userCredits}</span>
            <span className="text-gray-600">PENDIENTE: {totalCount - processedCount}</span>
          </div>
        </div>
      )}

      {/* ── Results Panels ── */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* LIVE Panel */}
        <div className="cyber-clip border border-green-500/40 bg-black/90 flex flex-col" style={{ minHeight: '320px' }}>
          <div className="flex items-center justify-between border-b border-green-900/50 px-5 py-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-400" />
              <h3 className="font-mono-cyber text-xs font-bold text-green-400 uppercase tracking-widest">APROBADAS — LIVE</h3>
            </div>
            <div className="flex items-center gap-2">
              {liveResults.length > 0 && (
                <>
                  <button onClick={copyAllLive} className="p-1 text-green-600 hover:text-green-400 cursor-pointer" title="Copiar todas">
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button onClick={removeAllLive} className="p-1 text-purple-700 hover:text-purple-400 cursor-pointer" title="Eliminar todas">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </>
              )}
              <span className="font-mono-cyber text-lg font-black text-green-400">{liveResults.length}</span>
            </div>
          </div>
          <div ref={liveRef} className="flex-1 overflow-y-auto p-3 space-y-1.5" style={{ maxHeight: '260px' }}>
            {liveResults.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="font-mono-cyber text-xs text-green-900 uppercase tracking-widest">Esperando resultados...</p>
              </div>
            ) : liveResults.map((r, i) => (
              <div key={i} className="flex flex-col gap-0.5 border border-green-900/40 bg-green-950/20 px-2 py-1.5 cyber-clip-alt group hover:border-green-500/60 transition-colors">
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-green-400 shrink-0" />
                  <span className="flex-1 font-mono-cyber text-xs text-green-300 break-all min-w-0">{r.card}</span>
                  {r.time_taken !== undefined && <span className="font-mono-cyber text-[9px] text-green-700 shrink-0">{r.time_taken}ms</span>}
                  <button onClick={() => copyToClipboard(r.card)} className="p-0.5 text-green-600 hover:text-green-400 cursor-pointer" title="Copiar">
                    <Copy className="h-3 w-3" />
                  </button>
                  <button onClick={() => removeLive(i)} className="p-0.5 text-purple-700 hover:text-purple-400 cursor-pointer" title="Eliminar">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
                {r.response && <span className="font-mono-cyber text-[10px] text-green-500 break-all pl-5">{r.response}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* DEAD Panel */}
        <div className="cyber-clip border border-purple-500/40 bg-black/90 flex flex-col" style={{ minHeight: '320px' }}>
          <div className="flex items-center justify-between border-b border-purple-900/50 px-5 py-3">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-purple-500" />
              <h3 className="font-mono-cyber text-xs font-bold text-purple-400 uppercase tracking-widest">RECHAZADAS — DEAD</h3>
            </div>
            <div className="flex items-center gap-2">
              {deadResults.length > 0 && (
                <>
                  <button onClick={copyAllDead} className="p-1 text-purple-600 hover:text-purple-400 cursor-pointer" title="Copiar todas">
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button onClick={removeAllDead} className="p-1 text-purple-700 hover:text-purple-400 cursor-pointer" title="Eliminar todas">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </>
              )}
              <span className="font-mono-cyber text-lg font-black text-purple-500">{deadResults.length}</span>
            </div>
          </div>
          <div ref={deadRef} className="flex-1 overflow-y-auto p-3 space-y-1.5" style={{ maxHeight: '260px' }}>
            {deadResults.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="font-mono-cyber text-xs text-purple-900 uppercase tracking-widest">Esperando resultados...</p>
              </div>
            ) : deadResults.map((r, i) => (
              <div key={i} className="flex flex-col gap-0.5 border border-purple-900/40 bg-purple-950/20 px-2 py-1.5 cyber-clip-alt group hover:border-purple-500/60 transition-colors">
                <div className="flex items-center gap-1">
                  <XCircle className="h-3 w-3 text-purple-500 shrink-0" />
                  <span className="flex-1 font-mono-cyber text-xs text-purple-300 break-all min-w-0">{r.card}</span>
                  {r.time_taken !== undefined && <span className="font-mono-cyber text-[9px] text-purple-700 shrink-0">{r.time_taken}ms</span>}
                  <button onClick={() => copyToClipboard(r.card)} className="p-0.5 text-purple-600 hover:text-purple-400 cursor-pointer" title="Copiar">
                    <Copy className="h-3 w-3" />
                  </button>
                  <button onClick={() => removeDead(i)} className="p-0.5 text-purple-700 hover:text-purple-400 cursor-pointer" title="Eliminar">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
                {r.response && <span className="font-mono-cyber text-[10px] text-purple-500 break-all pl-5">{r.response}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Shopify Config Modal ── */}
      {showShopifyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl cyber-clip border border-orange-500/50 bg-black p-6 shadow-[0_0_30px_rgba(249,115,22,0.3)] matrix-bg max-h-[90vh] overflow-y-auto">
            <button onClick={() => setShowShopifyModal(false)} className="absolute right-4 top-4 text-orange-500 hover:text-orange-400">
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-orange-900/50 pb-4">
              <Settings className="h-6 w-6 text-orange-500" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest neon-text-orange">CONFIGURACIÓN SHOPIFY</h2>
            </div>

            <div className="space-y-6">
              {/* URL Section */}
              <div>
                <label className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-orange-400">
                  <Globe className="h-3 w-3" /> SITIO WEB
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={siteUrlInput}
                    onChange={(e) => { setSiteUrlInput(e.target.value); setShopifyVerified(false) }}
                    placeholder="> https://tusitio.com"
                    className="flex-1 border border-orange-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-orange-400 placeholder-orange-900/50 focus:border-orange-400 focus:outline-none"
                  />
                  <button onClick={() => handleVerifySite()} disabled={shopifyLoading || !siteUrlInput.trim()}
                    className="cyber-clip-alt border border-orange-500/50 bg-orange-950/40 px-6 py-2 font-mono-cyber text-xs font-bold text-orange-400 transition-all hover:bg-orange-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer whitespace-nowrap">
                    {shopifyLoading ? 'VERIFICANDO...' : 'VERIFICAR'}
                  </button>
                </div>
                {shopifyError && (
                  <p className="mt-2 font-mono-cyber text-[10px] text-purple-400">{shopifyError}</p>
                )}
              </div>

              {/* Products Section */}
              {shopifyVerified && (
                <div>
                  <div className="mb-3 flex items-center justify-between border-b border-orange-900/30 pb-2">
                    <div className="flex items-center gap-2">
                      <ShoppingBag className="h-4 w-4 text-orange-400" />
                      <span className="font-mono-cyber text-[10px] font-bold uppercase tracking-widest text-orange-400">PRODUCTOS</span>
                      <span className="font-mono-cyber text-[10px] text-orange-700">({filteredProducts.length} de {shopifyProducts.length})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={shopifySearch}
                        onChange={(e) => { setShopifySearch(e.target.value); setShopifyPage(1) }}
                        onKeyDown={(e) => { if (e.key === 'Enter') setShopifyPage(1) }}
                        placeholder="Buscar producto..."
                        className="w-36 border border-orange-900/50 bg-black/50 px-2 py-1 font-mono-cyber text-[10px] text-orange-400 placeholder-orange-900/50 focus:border-orange-400 focus:outline-none"
                      />
                      <button
                        onClick={() => setShopifyPage(1)}
                        className="border border-orange-900/50 bg-orange-950/30 px-2 py-1 font-mono-cyber text-[10px] font-bold text-orange-400 hover:bg-orange-600 hover:text-white transition-all cursor-pointer"
                      >
                        BUSCAR
                      </button>
                    </div>
                  </div>

                  {shopifyLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
                    </div>
                  ) : shopifyProducts.length === 0 ? (
                    <p className="font-mono-cyber text-xs text-orange-700 italic py-8 text-center">
                      No se encontraron productos en este sitio.
                    </p>
                  ) : filteredProducts.length === 0 ? (
                    <p className="font-mono-cyber text-xs text-orange-700 italic py-8 text-center">
                      No se encontraron productos con ese término de búsqueda.
                    </p>
                  ) : (
                    <>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {pagedProducts.map((product) => {
                          const isSelected = selectedProduct?.id === product.id
                          const minPrice = product.variants.reduce((min, v) => {
                            const p = parseFloat(v.price)
                            return p < min ? p : min
                          }, Infinity)
                          const maxPrice = product.variants.reduce((max, v) => {
                            const p = parseFloat(v.price)
                            return p > max ? p : max
                          }, -Infinity)
                          const priceDisplay = minPrice === maxPrice
                            ? `$${minPrice}`
                            : `$${minPrice} - $${maxPrice}`

                          return (
                            <button
                              key={product.id}
                              onClick={() => setSelectedProduct(
                                isSelected ? null : product
                              )}
                              className={`flex flex-col cyber-clip-alt border p-2 transition-all text-left cursor-pointer ${isSelected
                                ? 'border-orange-400 bg-orange-950/40 shadow-[0_0_10px_rgba(249,115,22,0.3)]'
                                : 'border-orange-900/40 bg-orange-950/10 hover:border-orange-500/60'
                                }`}
                            >
                              <div className="relative aspect-square w-full bg-black/50 overflow-hidden mb-2">
                                {product.image ? (
                                  <img src={product.image} alt={product.title} className="h-full w-full object-cover" />
                                ) : (
                                  <div className="flex h-full items-center justify-center">
                                    <ShoppingBag className="h-8 w-8 text-orange-800" />
                                  </div>
                                )}
                                {isSelected && (
                                  <div className="absolute top-1 right-1 h-5 w-5 rounded-full bg-orange-500 flex items-center justify-center">
                                    <span className="text-black text-[10px] font-bold">✓</span>
                                  </div>
                                )}
                              </div>
                              <p className="font-mono-cyber text-[10px] text-orange-300 line-clamp-2 min-h-[2.5em]">{product.title}</p>
                              <p className="font-mono-cyber text-[10px] text-green-400 mt-1">{priceDisplay}</p>
                            </button>
                          )
                        })}
                      </div>

                      {/* Pagination */}
                      <div className="mt-4 flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleLoadShopifyPage(1)}
                          disabled={shopifyPage <= 1}
                          className="flex items-center gap-1 border border-orange-900/50 bg-orange-950/20 px-3 py-1.5 font-mono-cyber text-[10px] font-bold text-orange-400 transition-all hover:bg-orange-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                        >
                          {'<<'}
                        </button>
                        <button
                          onClick={() => handleLoadShopifyPage(shopifyPage - 1)}
                          disabled={shopifyPage <= 1}
                          className="flex items-center gap-1 border border-orange-900/50 bg-orange-950/20 px-3 py-1.5 font-mono-cyber text-[10px] font-bold text-orange-400 transition-all hover:bg-orange-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                        >
                          <ChevronLeft className="h-3 w-3" />
                        </button>
                        <span className="font-mono-cyber text-[10px] text-orange-600 px-3">
                          PÁGINA {shopifyPage} / {totalPages}
                        </span>
                        <button
                          onClick={() => handleLoadShopifyPage(shopifyPage + 1)}
                          disabled={shopifyPage >= totalPages}
                          className="flex items-center gap-1 border border-orange-900/50 bg-orange-950/20 px-3 py-1.5 font-mono-cyber text-[10px] font-bold text-orange-400 transition-all hover:bg-orange-600 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                        >
                          <ChevronRight className="h-3 w-3" />
                        </button>
                        <span className="font-mono-cyber text-[10px] text-orange-600">
                          {shopifyPage >= totalPages ? 'FIN' : '...'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Selected Product Summary */}
              {selectedProduct && (
                <div className="border border-green-500/30 bg-green-950/20 p-3 cyber-clip-alt">
                  <p className="font-mono-cyber text-[10px] font-bold text-green-400 uppercase tracking-widest mb-2">Producto Seleccionado</p>
                  <div className="flex items-center gap-3">
                    {selectedProduct.image && (
                      <img src={selectedProduct.image} alt="" className="h-10 w-10 object-cover border border-green-900/50" />
                    )}
                    <div>
                      <p className="font-mono-cyber text-xs text-green-300">{selectedProduct.title}</p>
                      <p className="font-mono-cyber text-[10px] text-green-600">Handle: {selectedProduct.handle}</p>
                      <p className="font-mono-cyber text-[10px] text-green-500 mt-0.5">
                        Variantes: {selectedProduct.variants.map(v => `${v.title} ($${v.price})`).join(', ')}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Address Checkbox + Fields */}
            <div className="border border-blue-900/30 bg-blue-950/10 p-3 cyber-clip-alt space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <button
                  type="button"
                  onClick={() => setModalSendAddr(!modalSendAddr)}
                  className={`h-5 w-5 border flex items-center justify-center transition-colors cursor-pointer ${modalSendAddr ? 'bg-blue-500 border-blue-400' : 'bg-black/50 border-blue-900/50'
                    }`}
                >
                  {modalSendAddr && <span className="text-white text-[10px] font-bold">✓</span>}
                </button>
                <div className="flex-1">
                  <p className="font-mono-cyber text-xs font-bold text-blue-300 uppercase tracking-widest">
                    ENVIAR DIRECCIÓN DE RESIDENCIA
                  </p>
                  <p className="font-mono-cyber text-[10px] text-blue-700 mt-0.5">
                    Si marcas esta opción se enviarán los datos de residencia al gate.
                    Si no, se enviará <span className="text-purple-400">"false"</span>.
                  </p>
                </div>
              </label>

              {modalSendAddr && (
                <div className="grid grid-cols-2 gap-3 border-t border-blue-900/30 pt-3">
                  <div className="col-span-2">
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">DIRECCIÓN / CALLE</label>
                    <input type="text" value={modalAddrStreet} onChange={(e) => setModalAddrStreet(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="Calle y número" />
                  </div>
                  <div>
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">CIUDAD</label>
                    <input type="text" value={modalAddrCity} onChange={(e) => setModalAddrCity(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="Ciudad" />
                  </div>
                  <div>
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">ESTADO</label>
                    <input type="text" value={modalAddrState} onChange={(e) => setModalAddrState(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="Estado" />
                  </div>
                  <div>
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">CÓDIGO POSTAL</label>
                    <input type="text" value={modalAddrZip} onChange={(e) => setModalAddrZip(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="CP" />
                  </div>
                  <div className="col-span-2">
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">NÚMERO DE CELULAR</label>
                    <input type="text" value={modalAddrPhone} onChange={(e) => setModalAddrPhone(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="+1 555 123 4567" />
                  </div>
                  <div className="col-span-2">
                    <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">CORREO ELECTRÓNICO</label>
                    <input type="email" value={modalAddrEmail} onChange={(e) => setModalAddrEmail(e.target.value)}
                      className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 placeholder-blue-900/50 focus:border-blue-400 focus:outline-none"
                      placeholder="correo@ejemplo.com" />
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="mt-6 flex gap-3 border-t border-orange-900/50 pt-4">
              <button
                onClick={() => {
                  if (!siteUrlInput.trim()) return
                  let baseUrl: string
                  try { baseUrl = new URL(siteUrlInput.trim()).origin } catch { return }
                  setShopifyConfig({
                    url: baseUrl,
                    sendAddress: modalSendAddr,
                    addrStreet: modalAddrStreet,
                    addrCity: modalAddrCity,
                    addrState: modalAddrState,
                    addrZip: modalAddrZip,
                    addrPhone: modalAddrPhone,
                    addrEmail: modalAddrEmail,
                    product: selectedProduct ? {
                      id: selectedProduct.id,
                      title: selectedProduct.title,
                      handle: selectedProduct.handle,
                      image: selectedProduct.image,
                      variant: selectedProduct.variants[0],
                    } : null,
                  })
                  setShowShopifyModal(false)
                }}
                disabled={!siteUrlInput.trim()}
                className="flex-1 cyber-clip-alt border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-green-400 transition-all hover:bg-green-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                GUARDAR CONFIGURACIÓN
              </button>
              <button onClick={() => setShowShopifyModal(false)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer">
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Credit Warning Modal ── */}
      {showCreditWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md cyber-clip border border-yellow-500/50 bg-black p-6 shadow-[0_0_30px_rgba(234,179,8,0.3)] matrix-bg">
            <div className="mb-6 flex items-center gap-3 border-b border-yellow-900/50 pb-4">
              <AlertTriangle className="h-6 w-6 text-yellow-500" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest">CRÉDITOS INSUFICIENTES</h2>
            </div>
            <div className="space-y-4">
              <div className="cyber-clip-alt border border-yellow-500/30 bg-yellow-950/20 p-4">
                <div className="flex items-center justify-between font-mono-cyber text-sm">
                  <span className="text-gray-400">Tus créditos:</span>
                  <span className="font-bold text-yellow-400">{creditWarningData.current}</span>
                </div>
                <div className="flex items-center justify-between font-mono-cyber text-sm mt-2">
                  <span className="text-gray-400">Costo máximo estimado:</span>
                  <span className="font-bold text-purple-400">{creditWarningData.worstCase}</span>
                </div>
              </div>
              <p className="font-mono-cyber text-xs text-gray-500">
                No tienes suficientes créditos para procesar todas las tarjetas en el peor de los casos.
              </p>
              <p className="font-mono-cyber text-xs text-yellow-600">
                ¿Deseas continuar de todas formas? El proceso se detendrá si te quedas sin créditos.
              </p>
            </div>
            <div className="mt-8 flex gap-3">
              <button onClick={() => creditWarningResolve.current?.(true)}
                className="flex-1 cyber-clip-alt border border-yellow-500/50 bg-yellow-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-yellow-400 transition-all hover:bg-yellow-600 hover:text-white cursor-pointer">
                CONTINUAR
              </button>
              <button onClick={() => creditWarningResolve.current?.(false)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer">
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Gen Data Modal ── */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md cyber-clip border border-purple-500/50 bg-black p-6 shadow-[0_0_30px_rgba(168,85,247,0.3)] matrix-bg">
            <button onClick={() => setShowGenModal(false)} className="absolute right-4 top-4 text-purple-500 hover:text-purple-400">
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-purple-900/50 pb-4">
              <Sparkles className="h-6 w-6 text-purple-500 animate-pulse" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest neon-text-purple">GENERADOR DE DATOS</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-500">BIN</label>
                <input type="text" value={genData.bin} onChange={(e) => setGenData({ ...genData, bin: e.target.value.replace(/[^0-9]/g, '').slice(0, 16) })}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none"
                  placeholder="Ej. 451234" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-500">MES</label>
                  <select value={genData.month} onChange={(e) => setGenData({ ...genData, month: e.target.value })}
                    className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-green-400 focus:border-green-500 focus:outline-none cursor-pointer appearance-none">
                    <option value="" className="bg-black text-green-600">Random</option>
                    {monthOptions.map(m => (
                      <option key={m} value={m} className="bg-black text-white">{m}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-orange-500">AÑO</label>
                  <select value={genData.year} onChange={(e) => setGenData({ ...genData, year: e.target.value })}
                    className="w-full border border-orange-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-orange-400 focus:border-orange-500 focus:outline-none cursor-pointer appearance-none">
                    <option value="" className="bg-black text-orange-600">Random</option>
                    {yearOptions.map(y => (
                      <option key={y} value={y} className="bg-black text-white">20{y}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-yellow-500">CVV</label>
                <input type="text" value={genData.cvv} onChange={(e) => setGenData({ ...genData, cvv: e.target.value })}
                  className="w-full border border-yellow-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-yellow-400 focus:border-yellow-500 focus:outline-none"
                  placeholder="Aleatorio" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-cyan-500">CANTIDAD</label>
                <input type="number" min="1" max="100" value={genData.quantity}
                  onChange={(e) => setGenData({ ...genData, quantity: e.target.value })}
                  className="w-full border border-cyan-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-cyan-400 focus:border-cyan-500 focus:outline-none"
                  placeholder="10" />
              </div>
              <p className="font-mono-cyber text-[10px] text-gray-600 italic">
                * Tarjetas generadas con algoritmo Luhn válido basado en el BIN ingresado.
              </p>
            </div>
            <div className="mt-8 flex gap-3">
              <button onClick={handleExecuteGen}
                className="flex-1 cyber-clip-alt border border-purple-500/50 bg-purple-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-purple-400 transition-all hover:bg-purple-600 hover:text-white cursor-pointer">
                GENERAR
              </button>
              <button onClick={() => setShowGenModal(false)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer">
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
