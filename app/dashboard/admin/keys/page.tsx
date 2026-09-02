'use client'

import { useEffect, useState } from 'react'
import { Terminal, Shield, Plus, Trash2, Pencil, X, Search, Copy, Check, Ticket, User, Calendar, KeyRound } from 'lucide-react'
import { toast } from '@/lib/toast'

interface Key {
  id: string
  key: string
  credits: number
  days: number
  rank: string
  isUsed: boolean
  usedById: string | null
  usedBy: { username: string } | null
  createdById: string | null
  createdBy: { username: string } | null
  createdAt: string
  usedAt: string | null
}

export default function AdminKeysPage() {
  const [keys, setKeys] = useState<Key[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'available' | 'used'>('all')
  const [showCreate, setShowCreate] = useState(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Form states
  const [createCredits, setCreateCredits] = useState(0)
  const [createDays, setCreateDays] = useState(30)
  const [createRank, setCreateRank] = useState('premium')
  const [createCount, setCreateCount] = useState(1)
  const [generating, setGenerating] = useState(false)

  // Edit states
  const [editModal, setEditModal] = useState<Key | null>(null)
  const [editCredits, setEditCredits] = useState(0)
  const [editDays, setEditDays] = useState(0)
  const [editRank, setEditRank] = useState('premium')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchKeys()
  }, [])

  async function fetchKeys() {
    try {
      const res = await fetch('/api/admin/keys')
      if (res.ok) {
        const data = await res.json()
        setKeys(data)
      } else {
        toast.error('Error al cargar las claves')
      }
    } catch {
      toast.error('Error al conectar con el servidor')
    }
    setLoading(false)
  }

  async function handleGenerateKeys() {
    setGenerating(true)
    try {
      const res = await fetch('/api/admin/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credits: createCredits,
          days: createDays,
          rank: createRank,
          count: createCount,
        }),
      })

      if (res.ok) {
        toast.success(`Se generaron ${createCount} claves exitosamente`)
        setShowCreate(false)
        setCreateCredits(0)
        setCreateDays(30)
        setCreateRank('user')
        setCreateCount(1)
        fetchKeys()
      } else {
        const data = await res.json()
        toast.error(data.error || 'Error al generar las claves')
      }
    } catch {
      toast.error('Error al conectar con el servidor')
    } finally {
      setGenerating(false)
    }
  }

  function openEdit(key: Key) {
    setEditModal(key)
    setEditCredits(key.credits)
    setEditDays(key.days)
    setEditRank(key.rank)
  }

  async function handleEditKey() {
    if (!editModal) return
    setSaving(true)
    try {
      const res = await fetch('/api/admin/keys', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: editModal.id,
          credits: editCredits,
          days: editDays,
          rank: editRank,
        }),
      })
      if (res.ok) {
        toast.success('Clave actualizada correctamente')
        setEditModal(null)
        fetchKeys()
      } else {
        const data = await res.json()
        toast.error(data.error || 'Error al actualizar la clave')
      }
    } catch {
      toast.error('Error de conexión')
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteKey(id: string, keyString: string) {
    if (!confirm(`¿Eliminar la clave "${keyString}"?`)) return

    try {
      const res = await fetch('/api/admin/keys', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      })

      if (res.ok) {
        toast.success('Clave eliminada correctamente')
        fetchKeys()
      } else {
        const data = await res.json()
        toast.error(data.error || 'Error al eliminar la clave')
      }
    } catch {
      toast.error('Error de conexión')
    }
  }

  function handleCopy(keyText: string) {
    navigator.clipboard.writeText(keyText)
    setCopiedKey(keyText)
    toast.success('Clave copiada al portapapeles')
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const filtered = keys.filter((k) => {
    const matchesSearch = k.key.toLowerCase().includes(search.toLowerCase()) || 
      (k.usedBy?.username.toLowerCase().includes(search.toLowerCase()) ?? false)
    
    if (filter === 'available') return matchesSearch && !k.isUsed
    if (filter === 'used') return matchesSearch && k.isUsed
    return matchesSearch
  })

  if (loading) return <div className="matrix-bg rounded-xl min-h-[400px]" />

  return (
    <div className="space-y-4">
      {/* Header filters and search */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`border px-4 py-1.5 font-mono-cyber text-xs tracking-wider transition-all cursor-pointer ${
              filter === 'all'
                ? 'border-red-500 bg-red-950/40 text-red-400'
                : 'border-gray-800 bg-black/40 text-gray-500 hover:text-gray-300'
            }`}
          >
            TODAS ({keys.length})
          </button>
          <button
            onClick={() => setFilter('available')}
            className={`border px-4 py-1.5 font-mono-cyber text-xs tracking-wider transition-all cursor-pointer ${
              filter === 'available'
                ? 'border-green-500 bg-green-950/40 text-green-400'
                : 'border-gray-800 bg-black/40 text-gray-500 hover:text-gray-300'
            }`}
          >
            DISPONIBLES ({keys.filter((k) => !k.isUsed).length})
          </button>
          <button
            onClick={() => setFilter('used')}
            className={`border px-4 py-1.5 font-mono-cyber text-xs tracking-wider transition-all cursor-pointer ${
              filter === 'used'
                ? 'border-blue-500 bg-blue-950/40 text-blue-400'
                : 'border-gray-800 bg-black/40 text-gray-500 hover:text-gray-300'
            }`}
          >
            USADAS ({keys.filter((k) => k.isUsed).length})
          </button>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex items-center gap-2 border border-gray-800 bg-black/50 px-3 py-1.5">
            <Search className="h-3.5 w-3.5 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por clave o usuario..."
              className="bg-transparent font-mono-cyber text-xs text-gray-300 placeholder-gray-700 focus:outline-none w-full sm:w-56"
            />
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center justify-center gap-1.5 border border-red-500/50 bg-red-950/40 px-4 py-2 font-mono-cyber text-xs font-bold text-red-400 hover:bg-red-600 hover:text-white transition-all cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" /> GENERAR KEYS
          </button>
        </div>
      </div>

      {/* Keys Table */}
      <div className="overflow-x-auto cyber-clip border border-red-500/30 bg-black/90">
        <table className="w-full text-left font-mono-cyber text-xs">
          <thead>
            <tr className="border-b border-red-900/50 bg-red-950/20">
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Código Key</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Rango</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Créditos</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Días de Membresía</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Estado</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Creado Por</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Creado En</th>
              <th className="px-4 py-3 text-red-400 uppercase tracking-widest">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((k) => (
              <tr key={k.id} className="border-b border-gray-800 hover:bg-red-950/10 transition-colors">
                <td className="px-4 py-3 font-bold text-white flex items-center gap-2">
                  <span className="font-mono text-sm tracking-wider">{k.key}</span>
                  <button
                    onClick={() => handleCopy(k.key)}
                    className="text-gray-500 hover:text-red-400 transition-colors p-1"
                    title="Copiar Clave"
                  >
                    {copiedKey === k.key ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <span className={`uppercase font-bold text-[10px] ${
                    k.rank === 'admin' ? 'text-red-400' :
                    k.rank === 'moderador' ? 'text-purple-400' :
                    k.rank === 'seller' ? 'text-blue-400' :
                    k.rank === 'vip' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {k.rank}
                  </span>
                </td>
                <td className="px-4 py-3 text-yellow-400 font-bold">
                  {k.credits > 0 ? `+${k.credits}` : '0'}
                </td>
                <td className="px-4 py-3 text-blue-400">
                  {k.days > 0 ? `+${k.days} días` : 'Sin cambio'}
                </td>
                <td className="px-4 py-3">
                  {k.isUsed ? (
                    <div className="flex flex-col gap-0.5">
                      <span className="inline-flex items-center gap-1 text-[10px] text-blue-400 uppercase">
                        <User className="h-2.5 w-2.5" /> Canjeado por {k.usedBy?.username}
                      </span>
                      {k.usedAt && (
                        <span className="text-[9px] text-gray-600 flex items-center gap-1">
                          <Calendar className="h-2.5 w-2.5" /> {new Date(k.usedAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="inline-flex items-center gap-1 border border-green-500/30 bg-green-950/20 px-2 py-0.5 text-[9px] text-green-400 font-bold uppercase">
                      Disponible
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-400 text-[10px] flex items-center gap-1">
                    <User className="h-2.5 w-2.5" /> {k.createdBy?.username ?? '—'}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(k.createdAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}
                </td>
                <td className="px-4 py-3">
                  {!k.isUsed ? (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEdit(k)}
                        className="flex items-center gap-1 border border-blue-500/50 bg-blue-950/40 px-3 py-1 text-blue-400 hover:bg-blue-600 hover:text-white transition-all cursor-pointer text-[10px] font-bold uppercase"
                      >
                        <Pencil className="h-3 w-3" /> Editar
                      </button>
                      <button
                        onClick={() => handleDeleteKey(k.id, k.key)}
                        className="flex items-center gap-1 border border-red-500/50 bg-red-950/40 px-3 py-1 text-red-400 hover:bg-red-600 hover:text-white transition-all cursor-pointer text-[10px] font-bold uppercase"
                      >
                        <Trash2 className="h-3 w-3" /> Eliminar
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-600 italic">No disponible</span>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-500 font-mono-cyber italic">
                  No se encontraron claves de activación.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Key Modal */}
      {editModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg cyber-clip border border-blue-500/50 bg-black p-6 shadow-[0_0_30px_rgba(59,130,246,0.2)] matrix-bg">
            <button
              onClick={() => setEditModal(null)}
              className="absolute right-4 top-4 text-red-500 hover:text-red-400 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-blue-900/50 pb-4">
              <Pencil className="h-6 w-6 text-blue-400" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest">
                EDITAR CLAVE
              </h2>
            </div>
            <div className="space-y-4">
              <div className="border border-gray-800 bg-black/50 p-3">
                <p className="font-mono-cyber text-[10px] uppercase text-gray-500 mb-1">Código</p>
                <p className="font-mono text-sm text-white tracking-wider">{editModal.key}</p>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Rango</label>
                <select
                  value={editRank}
                  onChange={(e) => setEditRank(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none cursor-pointer"
                >
                  <option value="premium">premium</option>
                  <option value="vip">vip</option>
                  <option value="seller">seller</option>
                  <option value="moderador">moderador</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-yellow-400">Créditos</label>
                  <input
                    type="number"
                    value={editCredits}
                    onChange={(e) => setEditCredits(Math.max(0, Number(e.target.value)))}
                    className="w-full border border-yellow-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-yellow-400 focus:border-yellow-500 focus:outline-none"
                    min={0}
                  />
                </div>
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">Días de Membresía</label>
                  <input
                    type="number"
                    value={editDays}
                    onChange={(e) => setEditDays(Math.max(0, Number(e.target.value)))}
                    className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 focus:border-blue-500 focus:outline-none"
                    min={0}
                  />
                </div>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button
                onClick={handleEditKey}
                className="flex-1 cyber-clip-alt border border-blue-500/50 bg-blue-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-blue-400 transition-all hover:bg-blue-600 hover:text-white cursor-pointer"
                disabled={saving}
              >
                {saving ? 'GUARDANDO...' : 'GUARDAR CAMBIOS'}
              </button>
              <button
                onClick={() => setEditModal(null)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer"
                disabled={saving}
              >
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Keys Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg cyber-clip border border-red-500/50 bg-black p-6 shadow-[0_0_30px_rgba(239,68,68,0.2)] matrix-bg">
            <button
              onClick={() => setShowCreate(false)}
              className="absolute right-4 top-4 text-red-500 hover:text-red-400 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-red-900/50 pb-4">
              <KeyRound className="h-6 w-6 text-red-500" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest">
                GENERAR CLAVES DE ACTIVACIÓN
              </h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-red-400">Rango a Otorgar</label>
                <select
                  value={createRank}
                  onChange={(e) => setCreateRank(e.target.value)}
                  className="w-full border border-red-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-red-500 focus:outline-none cursor-pointer"
                >
                  <option value="premium">premium</option>
                  <option value="vip">vip</option>
                  <option value="seller">seller</option>
                  <option value="moderador">moderador</option>
                  <option value="admin">admin</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-yellow-400">Créditos</label>
                  <input
                    type="number"
                    value={createCredits}
                    onChange={(e) => setCreateCredits(Math.max(0, Number(e.target.value)))}
                    className="w-full border border-yellow-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-yellow-400 focus:border-yellow-500 focus:outline-none"
                    min={0}
                  />
                </div>
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">Días de Membresía</label>
                  <input
                    type="number"
                    value={createDays}
                    onChange={(e) => setCreateDays(Math.max(0, Number(e.target.value)))}
                    className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 focus:border-blue-500 focus:outline-none"
                    min={0}
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-red-400">Cantidad a Generar</label>
                <input
                  type="number"
                  value={createCount}
                  onChange={(e) => setCreateCount(Math.min(50, Math.max(1, Number(e.target.value))))}
                  className="w-full border border-red-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-red-500 focus:outline-none"
                  min={1}
                  max={50}
                />
                <p className="mt-1 text-[9px] text-gray-600 font-mono-cyber">Límite: Máximo 50 claves por lote.</p>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button
                onClick={handleGenerateKeys}
                className="flex-1 cyber-clip-alt border border-red-500/50 bg-red-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-red-400 transition-all hover:bg-red-600 hover:text-white cursor-pointer"
                disabled={generating}
              >
                {generating ? 'GENERANDO...' : 'GENERAR'}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer"
                disabled={generating}
              >
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
