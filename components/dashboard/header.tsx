'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { Menu, Search, ChevronDown, LogOut, User as UserIcon, Zap, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface HeaderProps {
  onMenuClick?: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { data: session } = useSession()
  const router = useRouter()
  const [credits, setCredits] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/user/credits')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.credits !== undefined) setCredits(d.credits) })
      .catch(() => { })
  }, [])

  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent
      if (ce.detail !== undefined && typeof ce.detail === 'number')
        setCredits(ce.detail)
    }
    window.addEventListener('credits-updated', handler)
    return () => window.removeEventListener('credits-updated', handler)
  }, [])

  const handleLogout = async () => {
    await signOut({ redirect: false })
    router.push('/auth/login')
  }

  const displayName = session?.user?.name || 'Jill Chk'

  return (
    <header className="relative flex h-16 items-center justify-between border-b border-purple-900/30 bg-[#050505] px-6">
      {/* Bottom glow line */}
      <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />

      {/* Left side */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="text-gray-500 hover:bg-purple-900/20 hover:text-purple-400 lg:hidden cursor-pointer"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div className="hidden items-center gap-2 sm:flex">
          <div className="h-1.5 w-1.5 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
          <h2 className="font-mono text-sm font-bold tracking-wider text-white">
            JILL CHECKER
          </h2>
        </div>
      </div>

      {/* Search */}
      <div className="mx-4 flex-1 max-w-xl">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600 transition-colors group-focus-within:text-purple-500" />
          <Input
            placeholder="Buscar..."
            className="w-full border-purple-900/30 bg-[#0a0a0a] pl-10 font-mono text-sm text-white placeholder:text-gray-600 focus:border-purple-500/50 focus:ring-purple-500/20"
          />
          {/* Corner accents */}
          <div className="absolute -left-px -top-px h-2 w-2 border-l border-t border-purple-500/30 opacity-0 transition-opacity group-focus-within:opacity-100" />
          <div className="absolute -bottom-px -right-px h-2 w-2 border-b border-r border-purple-500/30 opacity-0 transition-opacity group-focus-within:opacity-100" />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex items-center gap-3 rounded-lg border border-transparent px-2 py-1 text-white transition-all hover:border-purple-900/30 hover:bg-purple-900/10 cursor-pointer"
            >
              <div className="relative">
                <div className="relative h-10 w-10 overflow-hidden rounded-full border-2 border-purple-600/50">
                  <Image
                    src="/images/avatar-capitan-black.jpg"
                    alt="User Avatar"
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#050505] bg-emerald-400">
                  <div className="absolute inset-0 animate-ping rounded-full bg-emerald-400 opacity-75" />
                </div>
              </div>
              <div className="hidden md:block">
                <p className="font-mono text-xs font-medium">{displayName}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="flex items-center gap-0.5 font-mono text-[10px] text-yellow-500">
                    <Zap className="h-2.5 w-2.5" /> {credits ?? '?'}
                  </span>
                  <span className="font-mono text-[10px] text-gray-600">|</span>
                  <span className={`flex items-center gap-0.5 font-mono text-[10px] uppercase ${session?.user?.rank === 'admin' ? 'text-purple-400' : 'text-gray-500'}`}>
                    <Shield className="h-2.5 w-2.5" /> {session?.user?.rank ?? 'user'}
                  </span>
                </div>
              </div>
              <ChevronDown className="h-4 w-4 text-gray-500" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-64 border-purple-900/30 bg-[#0a0a0a] text-white backdrop-blur-xl"
          >
            <div className="flex items-center gap-3 p-3">
              <div className="relative h-12 w-12 overflow-hidden rounded-full border border-purple-600/30">
                <Image
                  src="/images/avatar-capitan-black.jpg"
                  alt="User Avatar"
                  fill
                  className="object-cover"
                />
              </div>
              <div>
                <p className="font-mono text-sm font-medium">{displayName}</p>
                <p className="font-mono text-[10px] text-gray-500">@{session?.user?.name}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="flex items-center gap-1 font-mono text-[10px] text-yellow-500 uppercase">
                    <Zap className="h-3 w-3" /> {credits ?? '?'} créditos
                  </span>
                  <span className={`flex items-center gap-1 font-mono text-[10px] uppercase ${session?.user?.rank === 'admin' ? 'text-purple-400' : 'text-gray-500'}`}>
                    <Shield className="h-3 w-3" /> {session?.user?.rank ?? 'user'}
                  </span>
                </div>
              </div>
            </div>
            <DropdownMenuSeparator className="bg-purple-900/30" />
            <DropdownMenuItem className="font-mono text-xs hover:bg-purple-900/20 focus:bg-purple-900/20 cursor-pointer"
              onClick={() => router.push('/dashboard/perfil')}>
              <UserIcon className="mr-2 h-4 w-4 text-gray-500" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-purple-900/30" />
            <DropdownMenuItem
              className="font-mono text-xs text-purple-400 hover:bg-purple-900/20 hover:text-purple-300 focus:bg-purple-900/20 focus:text-purple-300 cursor-pointer"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Cerrar Sesion
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
