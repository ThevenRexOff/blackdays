'use client'

import { Server, Database, Globe, HardDrive, Mail, Clock } from 'lucide-react'

interface SystemItem {
  name: string
  description: string
  status: 'online' | 'warning' | 'offline'
  icon: 'server' | 'database' | 'api' | 'files' | 'mail' | 'backup'
}

const systemItems: SystemItem[] = [
  { name: 'Servidor Principal', description: 'Data Center 1', status: 'online', icon: 'server' },
  { name: 'Base de Datos', description: 'Cluster Primario', status: 'online', icon: 'database' },
  { name: 'API Gateway', description: 'Servicio Web', status: 'warning', icon: 'api' },
  { name: 'Servidor de Archivos', description: 'Data Center 2', status: 'online', icon: 'files' },
  { name: 'Servicio de Correo', description: 'Mail Transfer', status: 'online', icon: 'mail' },
  { name: 'Respaldo Automatico', description: 'Ultimo: 18 May 2024, 03:00', status: 'offline', icon: 'backup' },
]

const icons = {
  server: Server,
  database: Database,
  api: Globe,
  files: HardDrive,
  mail: Mail,
  backup: Clock,
}

const statusConfig = {
  online: { 
    label: 'ONLINE', 
    color: 'text-emerald-400', 
    bg: 'bg-emerald-400',
    glow: 'shadow-emerald-400/50'
  },
  warning: { 
    label: 'WARNING', 
    color: 'text-amber-400', 
    bg: 'bg-amber-400',
    glow: 'shadow-amber-400/50'
  },
  offline: { 
    label: 'OFFLINE', 
    color: 'text-gray-500', 
    bg: 'bg-gray-500',
    glow: ''
  },
}

export function SystemStatus() {
  return (
    <div className="group relative overflow-hidden rounded-lg border border-purple-900/30 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-5">
      {/* Corner decorations */}
      <div className="absolute left-0 top-0 h-10 w-10">
        <svg viewBox="0 0 40 40" className="h-full w-full">
          <path d="M0,0 L12,0 L12,2 L2,2 L2,12 L0,12 Z" fill="rgba(147, 51, 234, 0.3)" />
        </svg>
      </div>
      
      {/* Top glow line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
      
      <h3 className="relative mb-4 font-mono text-xs font-bold uppercase tracking-wider text-gray-400">
        Estado del Sistema
        <div className="absolute -left-5 top-1/2 h-px w-3 -translate-y-1/2 bg-purple-500/50" />
      </h3>
      
      <div className="space-y-2">
        {systemItems.map((item) => {
          const Icon = icons[item.icon]
          const status = statusConfig[item.status]
          
          return (
            <div 
              key={item.name} 
              className="group/item flex items-center justify-between rounded-md border border-transparent p-2 transition-all duration-200 hover:border-purple-900/20 hover:bg-purple-900/5"
            >
              <div className="flex items-center gap-3">
                <div className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-purple-900/20 bg-[#0a0a0a]">
                  <Icon className="h-4 w-4 text-gray-500" />
                  {/* Corner accent */}
                  <div className="absolute -right-px -top-px h-2 w-2 border-r border-t border-purple-500/30" />
                </div>
                <div>
                  <p className="font-mono text-xs font-medium text-white">{item.name}</p>
                  <p className="font-mono text-[10px] text-gray-600">{item.description}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-[#0a0a0a] px-2.5 py-1">
                <div className={`relative h-1.5 w-1.5 rounded-full ${status.bg} ${status.glow} shadow-sm`}>
                  {item.status === 'online' && (
                    <div className={`absolute inset-0 animate-ping rounded-full ${status.bg} opacity-75`} />
                  )}
                  {item.status === 'warning' && (
                    <div className={`absolute inset-0 animate-pulse rounded-full ${status.bg} opacity-75`} />
                  )}
                </div>
                <span className={`font-mono text-[10px] font-bold tracking-wider ${status.color}`}>
                  {status.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Bottom decorative line */}
      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-purple-900/30 to-transparent" />
    </div>
  )
}
