'use client'

import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { Terminal, Shield, Ban, UserCog, Search, Calendar, Plus, Trash2, X, RotateCcw } from 'lucide-react'

const privilegedRanks = ['admin', 'moderador', 'seller']

interface User {
  id: string
  username: string
  telegramId: string
  rank: string
  credits: number
  lives: number
  deads: number
  membershipExpiresAt: string | null
  createdAt: string
}

export default function AdminUsuariosPage() {
  const { data: session } = useSession()
  const currentRank = session?.user?.rank as string | undefined
  const isAdmin = currentRank === 'admin'
  const canEditPrivileged = isAdmin
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editCredits, setEditCredits] = useState(0)
  const [editRank, setEditRank] = useState('')
  const [editMembership, setEditMembership] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [createUsername, setCreateUsername] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createTelegram, setCreateTelegram] = useState('')
  const [createRank, setCreateRank] = useState('user')
  const [createCredits, setCreateCredits] = useState(0)
  const [createMembership, setCreateMembership] = useState('')

  useEffect(() => { fetchUsers() }, [])

  async function fetchUsers() {
    try {
      const res = await fetch('/api/admin/usuarios')
      if (res.ok) {
        const data = await res.json()
        setUsers(data)
      }
    } catch {}
    setLoading(false)
  }

  function isoDate(dateStr: string | null) {
    if (!dateStr) return ''
    try { return new Date(dateStr).toISOString().slice(0, 10) } catch { return '' }
  }

  function openEdit(user: User) {
    if (!canEditPrivileged && privilegedRanks.includes(user.rank)) return
    setEditId(user.id)
    setEditCredits(user.credits)
    setEditRank(user.rank)
    setEditMembership(isoDate(user.membershipExpiresAt))
  }

  async function saveUser(id: string) {
    const res = await fetch('/api/admin/usuarios', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id,
        credits: editCredits,
        rank: editRank,
        membershipExpiresAt: editMembership || null,
      }),
    })
    if (res.ok) {
      setEditId(null)
      fetchUsers()
    }
  }

  async function toggleBan(user: User) {
    const isBanned = user.rank === 'baneado'
    if (!confirm(`¿${isBanned ? 'Restaurar' : 'Banear'} al usuario "${user.username}"?`)) return
    await fetch('/api/admin/usuarios', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: user.id, rank: isBanned ? 'user' : 'baneado' }),
    })
    fetchUsers()
  }

  async function deleteUser(user: User) {
    if (!confirm(`¿Eliminar usuario "${user.username}"?`)) return
    await fetch('/api/admin/usuarios', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: user.id }),
    })
    fetchUsers()
  }

  async function createUser() {
    if (!createUsername.trim()) return
    await fetch('/api/admin/usuarios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: createUsername,
        password: createPassword || '123456',
        telegramId: createTelegram,
        rank: createRank,
        credits: createCredits,
        membershipExpiresAt: createMembership || null,
      }),
    })
    setShowCreate(false)
    setCreateUsername('')
    setCreatePassword('')
    setCreateTelegram('')
    setCreateRank('user')
    setCreateCredits(0)
    setCreateMembership('')
    fetchUsers()
  }

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.telegramId?.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return <div className="matrix-bg rounded-xl min-h-[300px]" />

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <p className="font-mono-cyber text-xs text-gray-500 flex items-center gap-2">
          <Terminal className="h-4 w-4" />
          {users.length} usuarios registrados
        </p>
        <div className="flex-1" />
        <div className="flex items-center gap-2 border border-gray-800 bg-black/50 px-3 py-1.5">
          <Search className="h-3.5 w-3.5 text-gray-500" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Buscar usuario..."
            className="bg-transparent font-mono-cyber text-xs text-gray-300 placeholder-gray-700 focus:outline-none w-40" />
        </div>
        {isAdmin && (
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-xs font-bold text-green-400 hover:bg-green-600 hover:text-white transition-all cursor-pointer">
            <Plus className="h-3.5 w-3.5" /> CREAR USUARIO
          </button>
        )}
      </div>

      <div className="overflow-x-auto cyber-clip border border-purple-500/30 bg-black/90">
        <table className="w-full text-left font-mono-cyber text-xs">
          <thead>
            <tr className="border-b border-purple-900/50 bg-purple-950/20">
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Usuario</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Telegram</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Rango</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Créditos</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">L/D</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Membresía</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Registro</th>
              <th className="px-4 py-3 text-purple-400 uppercase tracking-widest">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user) => (
              <tr key={user.id} className="border-b border-gray-800 hover:bg-purple-950/10 transition-colors">
                <td className="px-4 py-3">
                  <p className="font-bold text-white">{user.username}</p>
                  <p className="text-[9px] text-gray-600 mt-0.5">{user.id.slice(0, 12)}...</p>
                </td>
                <td className="px-4 py-3 text-blue-400">{user.telegramId || '—'}</td>
                <td className="px-4 py-3">
                  {editId === user.id ? (
                    <select value={editRank} onChange={e => setEditRank(e.target.value)}
                      className="border border-gray-700 bg-black/80 px-2 py-1 text-gray-300 cursor-pointer">
                      {canEditPrivileged ? (
                        <>
                          <option value="baneado">baneado</option>
                          <option value="user">user</option>
                          <option value="premium">premium</option>
                          <option value="vip">vip</option>
                          <option value="seller">seller</option>
                          <option value="moderador">moderador</option>
                          <option value="admin">admin</option>
                        </>
                      ) : (
                        <>
                          <option value="baneado">baneado</option>
                          <option value="user">user</option>
                          <option value="premium">premium</option>
                          <option value="vip">vip</option>
                        </>
                      )}
                    </select>
                  ) : (
                    <span className={`uppercase font-bold text-[10px] ${
                      user.rank === 'admin' ? 'text-purple-400' :
                      user.rank === 'moderador' ? 'text-purple-400' :
                      user.rank === 'seller' ? 'text-blue-400' :
                      user.rank === 'vip' ? 'text-yellow-400' :
                      user.rank === 'baneado' ? 'text-purple-600 line-through' :
                      'text-green-400'
                    }`}>
                      {user.rank === 'admin' ? <><Shield className="h-3 w-3 inline mr-1" />{user.rank}</> : user.rank}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {editId === user.id ? (
                    <input type="number" value={editCredits} onChange={e => setEditCredits(Number(e.target.value))}
                      className="w-20 border border-yellow-900/50 bg-black/50 px-2 py-1 text-yellow-400 text-center" />
                  ) : (
                    <span className="text-yellow-400 font-bold">{user.credits}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-green-500">{user.lives}</span>
                  <span className="text-gray-600">/</span>
                  <span className="text-purple-500">{user.deads}</span>
                </td>
                <td className="px-4 py-3">
                  {editId === user.id ? (
                    <input type="date" value={editMembership} onChange={e => setEditMembership(e.target.value)}
                      className="w-36 border border-blue-900/50 bg-black/50 px-2 py-1 text-blue-300 text-center" />
                  ) : (
                    <span className="text-gray-300 flex items-center gap-1">
                      <Calendar className="h-3 w-3 text-gray-600" />
                      {user.membershipExpiresAt
                        ? new Date(user.membershipExpiresAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
                        : '—'}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(user.createdAt).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}
                </td>
                <td className="px-4 py-3">
                  {editId === user.id ? (
                    <div className="flex items-center gap-1">
                      <button onClick={() => saveUser(user.id)}
                        className="px-3 py-1 border border-green-500/50 bg-green-950/40 text-green-400 hover:bg-green-600 hover:text-white cursor-pointer text-[10px] font-bold uppercase">Guardar</button>
                      <button onClick={() => setEditId(null)}
                        className="px-3 py-1 border border-gray-700 bg-black/60 text-gray-400 hover:bg-gray-800 cursor-pointer text-[10px] font-bold uppercase">Cancelar</button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      {canEditPrivileged || !privilegedRanks.includes(user.rank) ? (
                        <>
                          <button onClick={() => openEdit(user)}
                            className="flex items-center gap-1 border border-gray-700 bg-black/60 px-3 py-1 text-gray-400 hover:text-white hover:border-gray-500 transition-all cursor-pointer text-[10px] font-bold uppercase">
                            <UserCog className="h-3 w-3" /> Editar
                          </button>
                          <button onClick={() => toggleBan(user)}
                            className="flex items-center gap-1 border border-purple-500/50 bg-purple-950/40 px-3 py-1 text-purple-400 hover:bg-purple-600 hover:text-white transition-all cursor-pointer text-[10px] font-bold uppercase">
                            {user.rank === 'baneado' ? <><RotateCcw className="h-3 w-3" /></> : <><Ban className="h-3 w-3" /></>}
                          </button>
                          {isAdmin && (
                            <button onClick={() => deleteUser(user)}
                              className="flex items-center gap-1 border border-purple-500/50 bg-purple-950/40 px-3 py-1 text-purple-400 hover:bg-purple-600 hover:text-white transition-all cursor-pointer text-[10px] font-bold uppercase">
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </>
                      ) : (
                        <span className="text-gray-600 text-[10px] italic">Bloqueado</span>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg cyber-clip border border-green-500/50 bg-black p-6 shadow-[0_0_30px_rgba(34,197,94,0.2)] matrix-bg">
            <button onClick={() => setShowCreate(false)} className="absolute right-4 top-4 text-purple-500 hover:text-purple-400 cursor-pointer">
              <X className="h-5 w-5" />
            </button>
            <div className="mb-6 flex items-center gap-3 border-b border-green-900/50 pb-4">
              <Plus className="h-6 w-6 text-green-400" />
              <h2 className="font-mono-cyber text-lg font-bold text-white uppercase tracking-widest">CREAR USUARIO</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Usuario *</label>
                <input type="text" value={createUsername} onChange={e => setCreateUsername(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none" placeholder="Nombre de usuario" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Contraseña</label>
                <input type="text" value={createPassword} onChange={e => setCreatePassword(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none" placeholder="Default: 123456" />
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Telegram ID</label>
                <input type="text" value={createTelegram} onChange={e => setCreateTelegram(e.target.value)}
                  className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-green-400">Rango</label>
                  <select value={createRank} onChange={e => setCreateRank(e.target.value)}
                    className="w-full border border-green-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-white focus:border-green-500 focus:outline-none cursor-pointer">
                    {canEditPrivileged ? (
                      <>
                        <option value="baneado">baneado</option>
                        <option value="user">user</option>
                        <option value="premium">premium</option>
                        <option value="vip">vip</option>
                        <option value="seller">seller</option>
                        <option value="moderador">moderador</option>
                        <option value="admin">admin</option>
                      </>
                    ) : (
                      <>
                        <option value="baneado">baneado</option>
                        <option value="user">user</option>
                        <option value="premium">premium</option>
                        <option value="vip">vip</option>
                      </>
                    )}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-yellow-400">Créditos</label>
                  <input type="number" value={createCredits} onChange={e => setCreateCredits(Number(e.target.value))}
                    className="w-full border border-yellow-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-yellow-400 focus:border-yellow-500 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-mono-cyber text-[10px] uppercase text-blue-400">Membresía expira</label>
                <input type="date" value={createMembership} onChange={e => setCreateMembership(e.target.value)}
                  className="w-full border border-blue-900/50 bg-black/50 px-3 py-2 font-mono-cyber text-sm text-blue-300 focus:border-blue-500 focus:outline-none" />
                <p className="mt-1 text-[9px] text-gray-600 font-mono-cyber">Dejar vacío = Lifetime</p>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <button onClick={createUser}
                className="flex-1 cyber-clip-alt border border-green-500/50 bg-green-950/40 px-4 py-2 font-mono-cyber text-sm font-bold text-green-400 transition-all hover:bg-green-600 hover:text-white cursor-pointer">
                CREAR USUARIO
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
