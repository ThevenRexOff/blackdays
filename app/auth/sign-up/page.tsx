'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'
import { UserPlus, Terminal, Zap, Lock } from 'lucide-react'
import Image from 'next/image'
import { ParticleNetwork } from '@/components/auth/particles'

export default function SignUpPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [repeatPassword, setRepeatPassword] = useState('')
  const [telegramId, setTelegramId] = useState('')
  const [activationKey, setActivationKey] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    if (password !== repeatPassword) {
      setError('Las contraseñas no coinciden')
      setIsLoading(false)
      return
    }

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password,
          telegramId: telegramId || null,
          key: activationKey,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Error al crear la cuenta')
        return
      }

      router.push('/auth/login?message=Cuenta creada exitosamente. Inicia sesión para continuar.')
    } catch {
      setError('Error al crear la cuenta')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#050505]">
      <div className="absolute inset-0 opacity-15">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="signup-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(220, 38, 38, 0.15)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#signup-grid)" />
        </svg>
      </div>

      <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-red-600/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] bg-red-800/10 rounded-full blur-[120px] pointer-events-none" />

      <ParticleNetwork />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.03)_50%)] bg-[length:100%_4px] z-20" />

      <div className="relative z-10 flex flex-col items-center px-4">
        <div className="relative mb-6">
          <div className="relative h-36 w-36 md:h-44 md:w-44">
            <Image src="/images/trebol-logo.jpg" alt="Trebol Logo" fill className="rounded-full object-cover border-2 border-red-500/50 shadow-[0_0_30px_rgba(239,68,68,0.3)]" priority />
            <div className="absolute inset-0 -z-10 rounded-full bg-red-600/30 blur-3xl" />
          </div>
        </div>

        <h1 className="mb-1 text-center font-mono-cyber text-3xl font-bold tracking-[0.2em] text-white neon-text-red md:text-4xl">
          LOS PIRATAS
        </h1>
        <p className="mb-6 font-mono-cyber text-sm tracking-[0.3em] text-red-500">
          DE TREBOL
        </p>

        <div className="w-full max-w-md cyber-clip border border-red-500/50 bg-black/90 p-6 md:p-8 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
          <div className="mb-6 flex items-center justify-between border-b border-red-900/50 pb-4">
            <span className="font-mono-cyber text-sm tracking-widest text-red-400">
              <Terminal className="inline h-4 w-4 mr-2" />
              REGISTRO
            </span>
            <UserPlus className="h-5 w-5 text-red-500" />
          </div>

          <form onSubmit={handleSignUp} className="space-y-4">
            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-red-500">USUARIO</label>
              <Input
                type="text"
                placeholder="> Elige tu nombre de usuario..."
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-11 border-red-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-red-900/50 focus:border-red-500 focus:ring-red-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-red-500">TELEGRAM ID</label>
              <Input
                type="text"
                placeholder="> Tu ID de Telegram..."
                required
                value={telegramId}
                onChange={(e) => setTelegramId(e.target.value)}
                className="h-11 border-red-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-red-900/50 focus:border-red-500 focus:ring-red-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-red-500">CLAVE DE ACTIVACIÓN (KEY)</label>
              <Input
                type="text"
                placeholder="> TRBL-XXXX-XXXX-XXXX"
                required
                value={activationKey}
                onChange={(e) => setActivationKey(e.target.value)}
                className="h-11 border-red-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-red-900/50 focus:border-red-500 focus:ring-red-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-red-500">CONTRASEÑA</label>
              <Input
                type="password"
                placeholder="> Crea una contraseña segura..."
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 border-red-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-red-900/50 focus:border-red-500 focus:ring-red-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-red-500">REPETIR CONTRASEÑA</label>
              <Input
                type="password"
                placeholder="> Repite la contraseña..."
                required
                value={repeatPassword}
                onChange={(e) => setRepeatPassword(e.target.value)}
                className="h-11 border-red-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-red-900/50 focus:border-red-500 focus:ring-red-500/20"
              />
            </div>

            {error && (
              <div className="cyber-clip-alt border border-red-500/30 bg-red-950/20 p-3 font-mono-cyber text-xs text-red-400">
                ✗ {error}
              </div>
            )}

            <Button
              type="submit"
              className="h-11 w-full cyber-clip-alt bg-gradient-to-r from-red-700 to-red-600 font-mono-cyber text-sm tracking-widest text-white shadow-lg shadow-red-900/50 transition-all hover:from-red-600 hover:to-red-500 hover:shadow-[0_0_20px_rgba(239,68,68,0.5)] cursor-pointer"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2"><Zap className="h-4 w-4 animate-pulse" /> PROCESANDO...</span>
              ) : (
                <span className="flex items-center gap-2"><UserPlus className="h-4 w-4" /> UNIRSE</span>
              )}
            </Button>
          </form>

          <div className="mt-6 flex items-center justify-center gap-4 border-t border-red-900/30 pt-4">
            <Lock className="h-3 w-3 text-gray-600" />
            <Link href="/auth/login" className="font-mono-cyber text-xs text-red-500/80 transition-all hover:text-red-400 hover:neon-text-red">
              ¿Ya tienes acceso? Ingresa aquí
            </Link>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-3 cyber-clip-alt border border-red-900/30 bg-black/60 px-4 py-2">
          <div className="h-1.5 w-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse" />
          <span className="font-mono-cyber text-[10px] text-gray-600 uppercase tracking-widest">Nuevos reclutas bienvenidos — Autorización requerida</span>
        </div>
      </div>
    </div>
  )
}
