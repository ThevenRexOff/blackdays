import Image from 'next/image'
import { UserPlus, Package, FileText, Settings, Sparkles, Terminal } from 'lucide-react'

const quickActions = [
  { icon: UserPlus, label: 'Nuevo Usuario', color: 'from-emerald-500 to-emerald-600' },
  { icon: Package, label: 'Nuevo Producto', color: 'from-cyan-500 to-cyan-600' },
  { icon: FileText, label: 'Generar Reporte', color: 'from-violet-500 to-violet-600' },
  { icon: Settings, label: 'Configuracion', color: 'from-orange-500 to-orange-600' },
]

export function QuickActions() {
  return (
    <div className="group relative rounded-xl border border-purple-500/20 bg-gradient-to-br from-black/90 via-[#0a0808] to-black/90 p-5 backdrop-blur-xl overflow-hidden">
      {/* Cyber decorations */}
      <div className="absolute top-0 right-0 w-20 h-20">
        <div className="absolute top-2 right-2 w-12 h-12 border border-purple-500/20 rounded-lg rotate-45"></div>
        <div className="absolute top-4 right-4 w-8 h-8 border border-purple-500/30 rounded-md rotate-45"></div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Terminal className="w-4 h-4 text-purple-500" />
        <h3 className="text-sm font-bold uppercase tracking-wider text-purple-500">
          Accesos Rapidos
        </h3>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        {quickActions.map((action) => {
          const Icon = action.icon
          return (
            <button
              key={action.label}
              className="group/btn relative flex flex-col items-center gap-3 rounded-xl border border-purple-500/20 bg-black/50 p-4 transition-all duration-300 hover:border-purple-500/50 hover:bg-purple-500/5 hover:scale-105 overflow-hidden"
            >
              {/* Glow effect on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-purple-500/0 group-hover/btn:from-purple-500/10 group-hover/btn:to-transparent transition-all duration-300"></div>
              
              <div className={`relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${action.color} shadow-lg`}>
                <Icon className="h-6 w-6 text-white" />
              </div>
              <span className="relative text-xs font-medium text-gray-400 group-hover/btn:text-white transition-colors">{action.label}</span>
            </button>
          )
        })}
      </div>

      {/* Quote with ship illustration */}
      <div className="mt-6 relative">
        <div className="absolute -top-2 -left-2 text-purple-500/20">
          <Sparkles className="w-6 h-6" />
        </div>
        
        <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-transparent border border-purple-500/20">
          <div className="flex-1">
            <div className="text-purple-500 text-4xl font-serif leading-none mb-2 opacity-60">&ldquo;</div>
            <p className="text-sm text-gray-300 leading-relaxed italic">
              En los mares de los datos,<br />
              la informacion es nuestro tesoro.
            </p>
            <p className="mt-3 text-xs font-bold text-purple-500 tracking-wider">— JILL CHK</p>
          </div>
          <div className="relative w-28 h-24 flex-shrink-0">
            <div className="absolute -inset-2 bg-purple-500/20 rounded-xl blur-xl"></div>
            <Image
              src="/images/pirate-ship-illustration.jpg"
              alt="Pirate Ship"
              fill
              className="object-cover rounded-xl border border-purple-500/30 relative"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
