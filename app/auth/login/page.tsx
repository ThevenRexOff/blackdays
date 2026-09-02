'use client'

import { useState, Suspense } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'
import { Lock, Terminal, Zap } from 'lucide-react'
import Image from 'next/image'
import { ParticleNetwork } from '@/components/auth/particles'

function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const message = searchParams.get('message')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const result = await signIn('credentials', {
        username,
        password,
        redirect: false,
      })

      if (result?.error === 'AccessDenied') {
        setError('❌ HAS SIDO BANEADO DEL SISTEMA. Contacta al administrador.')
        setUsername('')
        setPassword('')
      } else if (result?.error === 'CredentialsSignin') {
        setError('Credenciales inválidas')
      } else if (result?.error) {
        setError('Credenciales inválidas')
      } else {
        setSuccess('¡Has iniciado sesión correctamente!')
        router.push('/dashboard')
        router.refresh()
      }
    } catch {
      setError('Error al iniciar sesión')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#050505]">
      <div className="absolute inset-0 opacity-15">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="login-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(147, 51, 234, 0.15)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#login-grid)" />
        </svg>
      </div>

      <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] bg-purple-800/10 rounded-full blur-[120px] pointer-events-none" />

      <ParticleNetwork />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.03)_50%)] bg-[length:100%_4px] z-20" />

      <div className="relative z-10 flex flex-col items-center px-4">
        <div className="relative mb-8">
          <div className="relative h-44 w-44 md:h-52 md:w-52">
            <Image src="/images/trebol-logo.jpg" alt="JILL CHK Logo" fill className="rounded-full object-cover border-2 border-purple-500/50 shadow-[0_0_30px_rgba(168,85,247,0.3)]" priority />
            <div className="absolute inset-0 -z-10 rounded-full bg-purple-600/30 blur-3xl" />
          </div>
        </div>

        <h1 className="mb-2 text-center font-mono-cyber text-4xl font-bold tracking-[0.2em] text-white neon-text-purple md:text-5xl">
          JILL CHK
        </h1>

        <div className="w-full max-w-md cyber-clip border border-purple-500/50 bg-black/90 p-8 shadow-[0_0_30px_rgba(168,85,247,0.15)]">
          <div className="mb-6 flex items-center justify-between border-b border-purple-900/50 pb-4">
            <span className="font-mono-cyber text-sm tracking-widest text-purple-400">
              <Terminal className="inline h-4 w-4 mr-2" />
              ACCESS TERMINAL
            </span>
            <Lock className="h-5 w-5 text-purple-500" />
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-purple-500">USUARIO</label>
              <Input
                type="text"
                placeholder="> Ingresa tu usuario..."
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-12 border-purple-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-purple-900/50 focus:border-purple-500 focus:ring-purple-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block font-mono-cyber text-[10px] uppercase tracking-widest text-purple-500">CONTRASEÑA</label>
              <Input
                type="password"
                placeholder="> ********"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12 border-purple-900/50 bg-black/50 font-mono-cyber text-sm text-white placeholder-purple-900/50 focus:border-purple-500 focus:ring-purple-500/20"
              />
            </div>

            {(message || success) && (
              <div className="cyber-clip-alt border border-green-500/30 bg-green-950/20 p-3 font-mono-cyber text-xs text-green-400">
                ✓ {message || success}
              </div>
            )}

            {error && (
              <div className="cyber-clip-alt border border-purple-500/30 bg-purple-950/20 p-3 font-mono-cyber text-xs text-purple-400">
                ✗ {error}
              </div>
            )}

            <Button
              type="submit"
              className="h-12 w-full cyber-clip-alt bg-gradient-to-r from-purple-700 to-purple-600 font-mono-cyber text-sm tracking-widest text-white shadow-lg shadow-purple-900/50 transition-all hover:from-purple-600 hover:to-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.5)] cursor-pointer"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2"><Zap className="h-4 w-4 animate-pulse" /> ACCEDIENDO...</span>
              ) : (
                <span className="flex items-center gap-2"><Zap className="h-4 w-4" /> INGRESAR</span>
              )}
            </Button>
          </form>

          <div className="mt-6 flex items-center justify-center gap-4 border-t border-purple-900/30 pt-4">
            <span className="font-mono-cyber text-[10px] text-gray-600">SIN ACCESO?</span>
            <Link href="/auth/sign-up" className="font-mono-cyber text-xs text-purple-500/80 transition-all hover:text-purple-400 hover:neon-text-purple">
              SOLICITAR ACCESO
            </Link>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-3 cyber-clip-alt border border-purple-900/30 bg-black/60 px-4 py-2">
          <div className="h-1.5 w-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)] animate-pulse" />
          <span className="font-mono-cyber text-[10px] text-gray-600 uppercase tracking-widest">Sistema en línea — Autorización requerida</span>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[#050505]">
        <div className="cyber-clip border border-purple-500/30 bg-black/80 px-8 py-4">
          <span className="font-mono-cyber text-sm text-purple-500 animate-pulse">INICIALIZANDO SISTEMA...</span>
        </div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
