'use client'

import { useState } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  TooltipProps,
  Area,
  AreaChart
} from 'recharts'

const data = [
  { date: '20 Abr', usuarios: 1200, ventas: 800 },
  { date: '27 Abr', usuarios: 1350, ventas: 950 },
  { date: '4 May', usuarios: 1500, ventas: 900 },
  { date: '11 May', usuarios: 1650, ventas: 1000 },
  { date: '18 May', usuarios: 1842, ventas: 1102 },
  { date: '25 May', usuarios: 2000, ventas: 1150 },
  { date: '1 Jun', usuarios: 2200, ventas: 1200 },
  { date: '8 Jun', usuarios: 2400, ventas: 1250 },
  { date: '15 Jun', usuarios: 2600, ventas: 1300 },
]

const timeRanges = ['7D', '30D', '90D', '1A']

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-purple-500/30 bg-[#0d0d0d]/95 p-4 shadow-xl backdrop-blur-sm">
        <div className="mb-3 flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-purple-500 animate-pulse" />
          <p className="font-mono text-xs uppercase tracking-wider text-purple-400">{label}</p>
        </div>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-6 py-1">
            <div className="flex items-center gap-2">
              <div 
                className="h-2 w-2 rounded-sm" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="font-mono text-xs text-gray-400">{entry.name}</span>
            </div>
            <span className="font-mono text-sm font-bold text-white">
              {entry.value?.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export function AnalyticsChart() {
  const [selectedRange, setSelectedRange] = useState('30D')

  return (
    <div className="group relative overflow-hidden rounded-lg border border-purple-900/30 bg-gradient-to-br from-[#0d0d0d] to-[#111111] p-5">
      {/* Corner decorations */}
      <div className="absolute left-0 top-0 h-12 w-12">
        <svg viewBox="0 0 48 48" className="h-full w-full">
          <path d="M0,0 L16,0 L16,2 L2,2 L2,16 L0,16 Z" fill="rgba(147, 51, 234, 0.3)" />
          <path d="M0,20 L8,20 L8,22 L0,22 Z" fill="rgba(147, 51, 234, 0.15)" />
        </svg>
      </div>
      <div className="absolute bottom-0 right-0 h-12 w-12 rotate-180">
        <svg viewBox="0 0 48 48" className="h-full w-full">
          <path d="M0,0 L16,0 L16,2 L2,2 L2,16 L0,16 Z" fill="rgba(147, 51, 234, 0.2)" />
        </svg>
      </div>

      {/* Top glow line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-500/40 to-transparent" />

      <div className="relative mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-white">ANALITICAS</h3>
          <div className="mt-3 flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50" />
              <span className="font-mono text-xs text-gray-400">Usuarios</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-gray-500" />
              <span className="font-mono text-xs text-gray-400">Ventas</span>
            </div>
          </div>
        </div>
        <div className="flex rounded-lg border border-purple-900/40 bg-[#080808] p-1">
          {timeRanges.map((range) => (
            <button
              key={range}
              onClick={() => setSelectedRange(range)}
              className={`rounded-md px-3 py-1.5 font-mono text-xs transition-all duration-200 ${
                selectedRange === range
                  ? 'bg-gradient-to-r from-purple-700 to-purple-600 text-white shadow-lg shadow-purple-900/30'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorUsuarios" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorVentas" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#666666" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#666666" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(147, 51, 234, 0.1)" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="#444" 
              tick={{ fill: '#555', fontSize: 11, fontFamily: 'monospace' }}
              axisLine={{ stroke: 'rgba(147, 51, 234, 0.2)' }}
              tickLine={{ stroke: 'rgba(147, 51, 234, 0.1)' }}
            />
            <YAxis 
              stroke="#444" 
              tick={{ fill: '#555', fontSize: 11, fontFamily: 'monospace' }}
              axisLine={{ stroke: 'rgba(147, 51, 234, 0.2)' }}
              tickLine={{ stroke: 'rgba(147, 51, 234, 0.1)' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="usuarios" 
              name="Usuarios"
              stroke="#a855f7" 
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorUsuarios)"
            />
            <Area 
              type="monotone" 
              dataKey="ventas" 
              name="Ventas"
              stroke="#666" 
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorVentas)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom decorative line */}
      <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-purple-900/30 to-transparent" />
    </div>
  )
}
