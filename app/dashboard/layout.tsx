'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/dashboard/sidebar'
import { Header } from '@/components/dashboard/header'
import { Toaster } from '@/components/ui/sonner'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-[#050505] relative overflow-hidden">
      {/* Animated circuit background */}
      <div className="absolute inset-0 pointer-events-none z-0 opacity-40">
        {/* Grid pattern */}
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="circuit-grid" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(147, 51, 234, 0.1)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#circuit-grid)" />
        </svg>
      </div>

      {/* Red glow effects */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-80 h-80 bg-purple-800/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Circuit decorations - Top Right */}
      <div className="absolute top-0 right-0 w-72 h-72 pointer-events-none z-0">
        <svg viewBox="0 0 200 200" className="w-full h-full">
          {/* Main corner frame */}
          <path d="M200,0 L150,0 L150,2 L198,2 L198,50 L200,50 Z" fill="rgba(147, 51, 234, 0.3)" />
          <path d="M200,8 L160,8 L160,10 L198,10 L198,40 L200,40 Z" fill="rgba(147, 51, 234, 0.2)" />

          {/* Circuit lines */}
          <path d="M200,60 L180,60 L170,70 L170,100" stroke="rgba(147, 51, 234, 0.3)" strokeWidth="1" fill="none" />
          <path d="M150,0 L150,30 L130,50 L130,80" stroke="rgba(147, 51, 234, 0.2)" strokeWidth="1" fill="none" />

          {/* Nodes */}
          <circle cx="170" cy="70" r="3" fill="rgba(147, 51, 234, 0.5)" />
          <circle cx="130" cy="50" r="2" fill="rgba(147, 51, 234, 0.4)" />
          <circle cx="180" cy="60" r="2" fill="rgba(147, 51, 234, 0.4)" />

          {/* Hexagon decoration */}
          <path d="M175,25 L185,30 L185,40 L175,45 L165,40 L165,30 Z"
            stroke="rgba(147, 51, 234, 0.25)" strokeWidth="1" fill="none" />
        </svg>
      </div>

      {/* Circuit decorations - Bottom Right */}
      <div className="absolute bottom-0 right-0 w-96 h-96 pointer-events-none z-0">
        <svg viewBox="0 0 300 300" className="w-full h-full">
          {/* Main corner frame */}
          <path d="M300,300 L300,240 L298,240 L298,298 L240,298 L240,300 Z" fill="rgba(147, 51, 234, 0.35)" />
          <path d="M300,230 L298,230 L298,298 L250,298 L250,300 L300,300 Z" fill="rgba(147, 51, 234, 0.2)" />

          {/* Diagonal lines */}
          <path d="M300,200 L200,300" stroke="rgba(147, 51, 234, 0.15)" strokeWidth="1" fill="none" />
          <path d="M300,170 L170,300" stroke="rgba(147, 51, 234, 0.1)" strokeWidth="1" fill="none" />
          <path d="M300,140 L140,300" stroke="rgba(147, 51, 234, 0.07)" strokeWidth="1" fill="none" />

          {/* Circuit paths */}
          <path d="M220,300 L220,270 L250,240 L300,240" stroke="rgba(147, 51, 234, 0.25)" strokeWidth="1" fill="none" />
          <path d="M300,260 L270,260 L260,270 L260,300" stroke="rgba(147, 51, 234, 0.2)" strokeWidth="1" fill="none" />

          {/* Nodes */}
          <circle cx="250" cy="240" r="3" fill="rgba(147, 51, 234, 0.5)" />
          <circle cx="260" cy="270" r="2" fill="rgba(147, 51, 234, 0.4)" />
          <circle cx="220" cy="270" r="2" fill="rgba(147, 51, 234, 0.4)" />

          {/* Data blocks */}
          <rect x="260" y="280" width="20" height="8" rx="1" fill="rgba(147, 51, 234, 0.15)" />
          <rect x="285" y="275" width="10" height="10" rx="1" stroke="rgba(147, 51, 234, 0.3)" fill="none" />
        </svg>
      </div>

      {/* Circuit decorations - Bottom Left */}
      <div className="absolute bottom-0 left-60 w-64 h-64 pointer-events-none z-0">
        <svg viewBox="0 0 200 200" className="w-full h-full">
          <path d="M0,200 L0,170 L2,170 L2,198 L30,198 L30,200 Z" fill="rgba(147, 51, 234, 0.2)" />
          <path d="M40,200 L40,180 L60,160 L100,160" stroke="rgba(147, 51, 234, 0.15)" strokeWidth="1" fill="none" />
          <circle cx="60" cy="160" r="2" fill="rgba(147, 51, 234, 0.3)" />
        </svg>
      </div>

      {/* Floating particles effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        {[...Array(15)].map((_, i) => {
          const r1 = Math.sin(i + 1) * 10000
          const r2 = Math.sin(i + 100) * 10000
          const r3 = Math.sin(i + 200) * 10000
          const r4 = Math.sin(i + 300) * 10000
          const rand1 = r1 - Math.floor(r1)
          const rand2 = r2 - Math.floor(r2)
          const rand3 = r3 - Math.floor(r3)
          const rand4 = r4 - Math.floor(r4)
          return (
            <div
              key={i}
              className="absolute w-1 h-1 bg-purple-500/40 rounded-full animate-pulse"
              style={{
                left: `${20 + rand1 * 60}%`,
                top: `${10 + rand2 * 80}%`,
                animationDelay: `${rand3 * 3}s`,
                animationDuration: `${2 + rand4 * 2}s`,
              }}
            />
          )
        })}
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 lg:static lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden relative z-10">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>

      {/* Scanline effect overlay */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.03)_50%)] bg-[length:100%_4px] z-50" />
      <Toaster />
    </div>
  )
}
