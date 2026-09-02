'use client'

import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { Shield } from 'lucide-react'

const allowedRanks = ['admin', 'moderador', 'seller']

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session || !allowedRanks.includes(session.user.rank as string)) {
      router.replace('/dashboard')
    } else {
      setChecked(true)
    }
  }, [session, status, router])

  if (status === 'loading' || !checked) {
    return (
      <div className="flex items-center justify-center min-h-[500px] matrix-bg rounded-xl">
        <div className="text-center space-y-4">
          <Shield className="h-12 w-12 text-purple-500 animate-pulse mx-auto" />
          <p className="font-mono-cyber text-sm text-purple-400">VERIFICANDO ACCESO...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 border-b border-purple-500/20 pb-4">
        <Shield className="h-8 w-8 text-purple-500" />
        <div>
          <h1 className="text-2xl font-black uppercase tracking-widest text-white neon-text-purple">ADMINISTRACIÓN</h1>
          <p className="font-mono-cyber text-xs text-purple-400/70">&gt; Panel de control administrativo</p>
        </div>
      </div>
      {children}
    </div>
  )
}
