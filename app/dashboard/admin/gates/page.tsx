'use client'

import { useEffect, useState } from 'react'
import { Terminal, CheckCircle2, XCircle, Activity, ArrowUpDown, Eye, EyeOff, Pencil, X, Save, Plus, Trash2 } from 'lucide-react'

interface GateStats {
  lives: number
  deads: number
  successRate: number
  total: number
}

interface Gate {
  id: string
  name: string
  category: string
  description: string
  isActive: boolean
  creditsLive: number
  creditsDead: number
  minRank: string
  threads: number
  apiUrl: string
  stats: GateStats
  createdAt: string
}

const categoryOptions = ['auth', 'charged', 'ccn', 'special', 'shopify', 'cookie', 'phone']
const rankOptions = ['premium', 'vip', 'seller', 'moderador', 'admin']

export default function AdminGatesPage() {
  const [gates, setGates] = useState<Gate[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editCreditsLive, setEditCreditsLive] = useState(0)
  const [editCreditsDead, setEditCreditsDead] = useState(0)
  const [editModal, setEditModal] = useState<Gate | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editApiUrl, setEditApiUrl] = useState('')
  const [editMinRank, setEditMinRank] = useState('premium')
  const [editThreads, setEditThreads] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createDesc, setCreateDesc] = useState('')
  const [createCategory, setCreateCategory] = useState('auth')
  const [createApiUrl, setCreateApiUrl] = useState('')
  const [createLive, setCreateLive] = useState(0)
  const [createDead, setCreateDead] = useState(0)
  const [createMinRank, setCreateMinRank] = useState('premium')
  const [createThreads, setCreateThreads] = useState(1)

  useEffect(() => { reload() }, [])

  function notifySidebar() {
    window.dispatchEvent(new CustomEvent('gates-updated'))
  }

  async function fetchGates() {
    try {
      const res = await fetch('/api/admin/gates')
      if (res.ok) {
        const data = await res.json()
        setGates(data.gates)
      }
    } catch {}
    setLoading(false)
  }

  async function reload() {
    await fetchGates()
    notifySidebar()
  }

  async function toggleActive(gate: Gate) {
    await fetch('/api/admin/gates', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: gate.id, isActive: !gate.isActive }),
    })
    reload()
  }

  async function saveCredits(id: string) {
    await fetch('/api/admin/gates', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, creditsLive: editCreditsLive, creditsDead: editCreditsDead }),
    })
    setEditingId(null)
    reload()
  }

  function openEdit(gate: Gate) {
    setEditModal(gate)
    setEditName(gate.name)
    setEditDesc(gate.description)
    setEditCategory(gate.category)
    setEditApiUrl(gate.apiUrl)
    setEditMinRank(gate.minRank)
    setEditThreads(gate.threads ?? 1)
  }

  async function saveEdit() {
    if (!editModal) return
    await fetch('/api/admin/gates', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: editModal.id,
        name: editName,
        description: editDesc,
        category: editCategory,
        apiUrl: editApiUrl,
        minRank: editMinRank,
        threads: editThreads,
      }),
    })
    setEditModal(null)
    reload()
  }

  async function deleteGate(gate: Gate) {
    if (!confirm(`¿Eliminar gate "${gate.name}"?`)) return
    await fetch('/api/admin/gates', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: gate.id }),
    })
    reload()
  }

  async function createGate() {
    if (!createName.trim()) return
    await fetch('/api/admin/gates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: createName,
        description: createDesc,
        category: createCategory,
        apiUrl: createApiUrl,
        creditsLive: createLive,
        creditsDead: createDead,
        minRank: createMinRank,
        threads: createThreads,
      }),
    })
    setShowCreate(false)
    setCreateName('')
    setCreateDesc('')
    setCreateCategory('auth')
    setCreateApiUrl('')
    setCreateLive(0)
    setCreateDead(0)
    setCreateMinRank('premium')
    setCreateThreads(1)
    reload()
  }

  if (loading) return <div className="matrix-bg rounded-xl min-h-[300px]" />

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-500 font-mono-cyber">
          <Terminal className="h-4 w-4" />
          <span>{gates.length} gates en el sistema</span>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-xs font-bold text-green-400 hover:bg-green-600 hover:text-white transition-all cursor-pointer">
          <Plus className="h-3.5 w-3.5" /> CREAR GATE
        </button>
      </div>

      <div className="overflow-x-auto cyber-clip border border-purple-500/30 bg-black/90">
        <table className="w-full text-left font-mono-cyber text-xs">
          <thead>
            <tr className="border-b border-purple-900/50 bg-purple-950/20">
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Gate</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Categoría</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Rango Min</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Estado</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Costo L/D</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Stats</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">SR</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {gates.map((gate) => (
              <tr key={gate.id} className="border-b border-gray-800 hover:bg-purple-950/10 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div>
                      <p className="font-bold text-white">{gate.name}</p>
                      <p className="text-[9px] text-gray-600 mt-0.5">{gate.id.slice(0, 12)}...</p>
                    </div>
                    <button onClick={() => openEdit(gate)}
                      className="p-1 text-gray-600 hover:text-purple-400 transition-colors cursor-pointer" title="Editar gate">
                      <Pencil className="h-3 w-3" />
                    </button>
                  </div>
                  {gate.apiUrl && <p className="text-[9px] text-blue-500 mt-0.5 truncate max-w-[200px]">{gate.apiUrl}</p>}
                </td>
                <td className="px-4 py-3 text-gray-400 uppercase">{gate.category}</td>
                <td className="px-4 py-3">
                  <span className={`uppercase font-bold text-[10px] ${
                    gate.minRank === 'admin' ? 'text-purple-400' :
                    gate.minRank === 'moderador' ? 'text-purple-400' :
                    gate.minRank === 'seller' ? 'text-blue-400' :
                    gate.minRank === 'vip' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>{gate.minRank}</span>
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => toggleActive(gate)} className="flex items-center gap-1.5 cursor-pointer">
                    {gate.isActive ? (
                      <span className="flex items-center gap-1 text-green-400 border border-green-900/40 bg-green-950/30 px-2 py-1">
                        <Eye className="h-3 w-3" /> Activo
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-purple-400 border border-purple-900/40 bg-purple-950/30 px-2 py-1">
                        <EyeOff className="h-3 w-3" /> Inactivo
                      </span>
                    )}
                  </button>
                </td>
                <td className="px-4 py-3">
                  {editingId === gate.id ? (
                    <div className="flex items-center gap-1">
                      <input type="number" value={editCreditsLive} onChange={e => setEditCreditsLive(Number(e.target.value))}
                        className="w-16 border border-green-900/50 bg-black/50 px-1 py-1 text-green-400 text-center" />
                      <span className="text-gray-600">/</span>
                      <input type="number" value={editCreditsDead} onChange={e => setEditCreditsDead(Number(e.target.value))}
                        className="w-16 border border-purple-900/50 bg-black/50 px-1 py-1 text-purple-400 text-center" />
                      <button onClick={() => saveCredits(gate.id)} className="px-2 py-1 border border-green-500/50 bg-green-950/40 text-green-400 hover:bg-green-600 hover:text-white cursor-pointer text-[10px]"><Save className="h-3 w-3 inline" /></button>
                      <button onClick={() => setEditingId(null)} className="px-2 py-1 border border-gray-700 bg-black/60 text-gray-400 hover:bg-gray-800 cursor-pointer text-[10px]"><X className="h-3 w-3 inline" /></button>
                    </div>
                  ) : (
                    <button onClick={() => { setEditingId(gate.id); setEditCreditsLive(gate.creditsLive); setEditCreditsDead(gate.creditsDead) }}
                      className="flex items-center gap-1 text-gray-300 hover:text-white cursor-pointer">
                      <span className="text-green-400">{gate.creditsLive}</span>
                      <span className="text-gray-600">/</span>
                      <span className="text-purple-400">{gate.creditsDead}</span>
                      <ArrowUpDown className="h-3 w-3 text-gray-600 ml-1" />
                    </button>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-0.5 text-green-400"><CheckCircle2 className="h-3 w-3" />{gate.stats.lives}</span>
                    <span className="text-gray-600">|</span>
                    <span className="flex items-center gap-0.5 text-purple-400"><XCircle className="h-3 w-3" />{gate.stats.deads}</span>
                    <span className="text-gray-600">|</span>
                    <span className="flex items-center gap-0.5 text-gray-400"><Activity className="h-3 w-3" />{gate.stats.total}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`font-bold ${gate.stats.successRate >= 50 ? 'text-green-400' : gate.stats.successRate > 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {gate.stats.successRate}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button onClick={() => toggleActive(gate)}
                      className={`px-3 py-1 border text-[10px] font-bold uppercase cursor-pointer transition-all ${
                        gate.isActive
                          ? 'border-purple-500/50 bg-purple-950/40 text-purple-400 hover:bg-purple-600 hover:text-white'
                          : 'border-green-500/50 bg-green-950/40 text-green-400 hover:bg-green-600 hover:text-white'
                      }`}>
                      {gate.isActive ? 'Desactivar' : 'Activar'}
                    </button>
                    <button onClick={() => openEdit(gate)}
                      className="px-3 py-1 border border-blue-500/50 bg-blue-950/40 text-blue-400 hover:bg-blue-600 hover:text-white text-[10px] font-bold uppercase cursor-pointer transition-all">
                      Editar
                    </button>
                    <button onClick={() => deleteGate(gate)}
                      className="px-3 py-1 border border-purple-500/50 bg-purple-950/40 text-purple-400 hover:bg-purple-600 hover:text-white text-[10px] font-bold uppercase cursor-pointer transition-all">
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg cyber-clip border border-purple-500/50 bg-black p-6 shadow-[0_0_30px_rgba(168,85,247,0.3)] matrix-bg">
            <button onClick={() => setEditModal(null)} className="absolute right-4 top-4 text-purple-500 hover:text-purple-400 cursor-pointer">
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-purple-900/50 pb-4">
              <Pencil className="h-6 w-6 text-purple-500" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest neon-text-purple">EDITAR GATE</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Nombre</label>
                <input type="text" value={editName} onChange={e => setEditName(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Descripción</label>
                <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} rows={3}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none resize-none" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Categoría</label>
                <select value={editCategory} onChange={e => setEditCategory(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none cursor-pointer">
                  {categoryOptions.map(c => (
                    <option key={c} value={c} className="bg-black text-white">{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">API URL</label>
                <input type="text" value={editApiUrl} onChange={e => setEditApiUrl(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none"
                  placeholder="https://..." />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Rango Mínimo Requerido</label>
                <select value={editMinRank} onChange={e => setEditMinRank(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none cursor-pointer">
                  {rankOptions.map(r => (
                    <option key={r} value={r} className="bg-black text-white">{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-cyan-400">Threads (máx 4)</label>
                <select value={editThreads} onChange={e => setEditThreads(Number(e.target.value))}
                  className="w-full border border-cyan-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-cyan-500 focus:outline-none cursor-pointer">
                  {[1, 2, 3, 4].map(t => (
                    <option key={t} value={t} className="bg-black text-white">{t} thread{t > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button onClick={saveEdit}
                className="flex-1 cyber-clip-alt border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-green-400 transition-all hover:bg-green-600 hover:text-white cursor-pointer">
                GUARDAR CAMBIOS
              </button>
              <button onClick={() => setEditModal(null)}
                className="flex-1 cyber-clip-alt border border-gray-700 bg-black/60 px-4 py-2 font-mono-cyber text-sm font-bold text-gray-400 transition-all hover:bg-gray-800 hover:text-white cursor-pointer">
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg cyber-clip border border-green-500/50 bg-black p-6 shadow-[0_0_30px_rgba(34,197,94,0.2)] matrix-bg">
            <button onClick={() => setShowCreate(false)} className="absolute right-4 top-4 text-purple-500 hover:text-purple-400 cursor-pointer">
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-green-900/50 pb-4">
              <Plus className="h-6 w-6 text-green-400" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest">CREAR GATE</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Nombre *</label>
                <input type="text" value={createName} onChange={e => setCreateName(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none" placeholder="Nombre del gate" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Descripción</label>
                <textarea value={createDesc} onChange={e => setCreateDesc(e.target.value)} rows={2}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none resize-none" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Categoría</label>
                <select value={createCategory} onChange={e => setCreateCategory(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none cursor-pointer">
                  {categoryOptions.map(c => (
                    <option key={c} value={c} className="bg-black text-white">{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">API URL</label>
                <input type="text" value={createApiUrl} onChange={e => setCreateApiUrl(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none" placeholder="https://..." />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Costo Live</label>
                  <input type="number" value={createLive} onChange={e => setCreateLive(Number(e.target.value))}
                    className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-green-400 focus:border-green-500 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Costo Dead</label>
                  <input type="number" value={createDead} onChange={e => setCreateDead(Number(e.target.value))}
                    className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-purple-400 focus:border-purple-500 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-purple-400">Rango Mínimo Requerido</label>
                <select value={createMinRank} onChange={e => setCreateMinRank(e.target.value)}
                  className="w-full border border-purple-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-purple-500 focus:outline-none cursor-pointer">
                  {rankOptions.map(r => (
                    <option key={r} value={r} className="bg-black text-white">{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-cyan-400">Threads (máx 4)</label>
                <select value={createThreads} onChange={e => setCreateThreads(Number(e.target.value))}
                  className="w-full border border-cyan-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-cyan-500 focus:outline-none cursor-pointer">
                  {[1, 2, 3, 4].map(t => (
                    <option key={t} value={t} className="bg-black text-white">{t} thread{t > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button onClick={createGate}
                className="flex-1 cyber-clip-alt border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-green-400 transition-all hover:bg-green-600 hover:text-white cursor-pointer">
                CREAR GATE
              </button>
              <button onClick={() => setShowCreate(false)}
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
