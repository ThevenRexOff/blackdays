'use client'

import { Users, ShoppingCart, DollarSign, Activity } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  change: string
  changeType: 'positive' | 'negative'
  icon: 'users' | 'sales' | 'revenue' | 'status'
  subtitle?: string
}

const icons = {
  users: Users,
  sales: ShoppingCart,
  revenue: DollarSign,
  status: Activity,
}

export function StatCard({ title, value, change, changeType, icon, subtitle }: StatCardProps) {
  const Icon = icons[icon]
  
  return (
    <div className="group relative overflow-hidden rounded-lg border border-red-900/30 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-5 transition-all duration-300 hover:border-red-700/40 hover:shadow-lg hover:shadow-red-900/10">
      {/* Corner decorations */}
      <div className="absolute left-0 top-0 h-8 w-8">
        <svg viewBox="0 0 32 32" className="h-full w-full">
          <path d="M0,0 L12,0 L12,2 L2,2 L2,12 L0,12 Z" fill="rgba(220, 38, 38, 0.3)" />
        </svg>
      </div>
      <div className="absolute bottom-0 right-0 h-8 w-8 rotate-180">
        <svg viewBox="0 0 32 32" className="h-full w-full">
          <path d="M0,0 L12,0 L12,2 L2,2 L2,12 L0,12 Z" fill="rgba(220, 38, 38, 0.2)" />
        </svg>
      </div>
      
      {/* Glow effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-red-600/0 via-red-600/5 to-red-600/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      
      {/* Scan line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-500/30 to-transparent" />
      
      <div className="relative flex items-start justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-gray-500">{title}</p>
          <p className="mt-2 font-mono text-3xl font-bold text-white">{value}</p>
          {subtitle ? (
            <p className="mt-1 font-mono text-sm text-emerald-400">{subtitle}</p>
          ) : (
            <p className={`mt-1 font-mono text-sm ${changeType === 'positive' ? 'text-emerald-400' : 'text-red-400'}`}>
              <span className="inline-flex items-center">
                {changeType === 'positive' ? (
                  <svg className="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l5-5 5 5M7 7l5 5 5-5" />
                  </svg>
                ) : (
                  <svg className="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-5 5-5-5M17 17l-5-5-5 5" />
                  </svg>
                )}
                {change}
              </span>
              <span className="ml-1 text-gray-600">vs ultimo mes</span>
            </p>
          )}
        </div>
        <div className="relative flex h-14 w-14 items-center justify-center">
          {/* Hexagonal icon container */}
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 56 56">
            <path 
              d="M28,2 L52,15 L52,41 L28,54 L4,41 L4,15 Z" 
              fill="rgba(220, 38, 38, 0.1)" 
              stroke="rgba(220, 38, 38, 0.3)"
              strokeWidth="1"
            />
          </svg>
          <Icon className="relative z-10 h-6 w-6 text-red-500" />
        </div>
      </div>
      
      {/* Bottom decorative line */}
      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-red-900/30 to-transparent" />
    </div>
  )
}
