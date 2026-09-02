'use client'

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

const data = [
  { name: 'Nuevos', value: 42, color: '#a855f7' },
  { name: 'Recurrentes', value: 37, color: '#666' },
  { name: 'Invitados', value: 21, color: '#333' },
]

export function UserDistribution() {
  return (
    <div className="group relative overflow-hidden rounded-lg border border-purple-900/30 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-5">
      {/* Corner decorations */}
      <div className="absolute right-0 top-0 h-10 w-10">
        <svg viewBox="0 0 40 40" className="h-full w-full">
          <path d="M40,0 L28,0 L28,2 L38,2 L38,12 L40,12 Z" fill="rgba(147, 51, 234, 0.3)" />
        </svg>
      </div>
      
      {/* Top glow line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
      
      <h3 className="relative mb-4 font-mono text-xs font-bold uppercase tracking-wider text-gray-400">
        Distribucion de Usuarios
        <div className="absolute -left-5 top-1/2 h-px w-3 -translate-y-1/2 bg-purple-500/50" />
      </h3>
      
      <div className="flex items-center gap-4">
        <div className="relative h-36 w-36">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={58}
                paddingAngle={3}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    style={{ filter: index === 0 ? 'url(#glow)' : 'none' }}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          
          {/* Center content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="relative">
              <span className="font-mono text-2xl font-bold text-white">2,845</span>
              <div className="absolute -inset-2 -z-10 rounded-full bg-purple-500/10 blur-md" />
            </div>
            <span className="mt-1 font-mono text-[10px] uppercase tracking-widest text-gray-500">TOTAL</span>
          </div>
          
          {/* Rotating ring decoration */}
          <div className="absolute inset-0 animate-[spin_20s_linear_infinite]">
            <svg viewBox="0 0 144 144" className="h-full w-full">
              <circle cx="72" cy="72" r="68" fill="none" stroke="rgba(147, 51, 234, 0.1)" strokeWidth="1" strokeDasharray="4 8" />
            </svg>
          </div>
        </div>
        
        <div className="flex-1 space-y-3">
          {data.map((item, index) => (
            <div key={item.name} className="group/item flex items-center justify-between rounded-md p-2 transition-colors hover:bg-purple-900/10">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div 
                    className="h-2.5 w-2.5 rounded-sm"
                    style={{ backgroundColor: item.color }}
                  />
                  {index === 0 && (
                    <div className="absolute inset-0 animate-ping rounded-sm bg-purple-500/50" />
                  )}
                </div>
                <span className="font-mono text-xs text-gray-400">{item.name}</span>
              </div>
              <span className="font-mono text-sm font-bold text-white">{item.value}%</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Bottom decorative line */}
      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-purple-900/30 to-transparent" />
    </div>
  )
}
