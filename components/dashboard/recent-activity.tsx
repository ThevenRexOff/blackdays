import Image from 'next/image'
import { MoreVertical, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ActivityItem {
  id: string
  user: string
  avatar: string
  action: 'CREO' | 'ACTUALIZO' | 'ELIMINO' | 'INICIO SESION'
  detail: string
  date: string
}

const activities: ActivityItem[] = [
  {
    id: '1',
    user: 'Barba Negra',
    avatar: '/images/avatar-barba-negra.jpg',
    action: 'CREO',
    detail: 'Nuevo usuario registrado: Calico Jack',
    date: '18 May 2024, 14:35',
  },
  {
    id: '2',
    user: 'Anne Bonny',
    avatar: '/images/avatar-anne-bonny.jpg',
    action: 'ACTUALIZO',
    detail: 'Actualizo la informacion del producto: Ron Premium',
    date: '18 May 2024, 13:21',
  },
  {
    id: '3',
    user: 'Capitan Black',
    avatar: '/images/avatar-capitan-black.jpg',
    action: 'ELIMINO',
    detail: 'Elimino el usuario: Long John Silver',
    date: '18 May 2024, 11:07',
  },
  {
    id: '4',
    user: 'Hacha',
    avatar: '/images/avatar-hacha.jpg',
    action: 'INICIO SESION',
    detail: 'Inicio de sesion exitoso',
    date: '18 May 2024, 09:42',
  },
]

const actionColors = {
  CREO: 'bg-emerald-500/80 shadow-emerald-500/50',
  ACTUALIZO: 'bg-cyan-500/80 shadow-cyan-500/50',
  ELIMINO: 'bg-purple-500/80 shadow-purple-500/50',
  'INICIO SESION': 'bg-violet-500/80 shadow-violet-500/50',
}

export function RecentActivity() {
  return (
    <div className="group relative rounded-xl border border-purple-500/20 bg-gradient-to-br from-black/90 via-[#0a0808] to-black/90 p-5 backdrop-blur-xl overflow-hidden">
      {/* Cyber corner accents */}
      <div className="absolute top-0 left-0 w-16 h-16">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-purple-500 to-transparent"></div>
        <div className="absolute top-0 left-0 w-[2px] h-full bg-gradient-to-b from-purple-500 to-transparent"></div>
      </div>
      <div className="absolute top-0 right-0 w-16 h-16">
        <div className="absolute top-0 right-0 w-full h-[2px] bg-gradient-to-l from-purple-500 to-transparent"></div>
        <div className="absolute top-0 right-0 w-[2px] h-full bg-gradient-to-b from-purple-500 to-transparent"></div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-purple-500" />
        <h3 className="text-sm font-bold uppercase tracking-wider text-purple-500">
          Actividad Reciente
        </h3>
        <div className="flex-1 h-[1px] bg-gradient-to-r from-purple-500/50 to-transparent ml-2"></div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-purple-500/20 text-left text-xs uppercase text-gray-500">
              <th className="pb-3 pr-4 font-medium tracking-wider">Usuario</th>
              <th className="pb-3 pr-4 font-medium tracking-wider">Accion</th>
              <th className="pb-3 pr-4 font-medium tracking-wider">Detalle</th>
              <th className="pb-3 pr-4 font-medium tracking-wider">Fecha</th>
              <th className="pb-3"></th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {activities.map((activity, index) => (
              <tr 
                key={activity.id} 
                className="border-b border-purple-500/10 transition-all duration-300 hover:bg-purple-500/5"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="absolute -inset-1 bg-purple-500/30 rounded-full blur-sm"></div>
                      <div className="relative h-9 w-9 overflow-hidden rounded-full border-2 border-purple-500/50 ring-2 ring-purple-500/20">
                        <Image
                          src={activity.avatar}
                          alt={activity.user}
                          fill
                          className="object-cover"
                        />
                      </div>
                    </div>
                    <span className="text-white font-medium">{activity.user}</span>
                  </div>
                </td>
                <td className="py-3 pr-4 flex-shrink-0">
                  <span className={`inline-block rounded-md px-3 py-1.5 text-xs font-bold text-white shadow-lg whitespace-nowrap ${actionColors[activity.action]}`}>
                    {activity.action}
                  </span>
                </td>
                <td className="py-3 pr-4 text-gray-400">{activity.detail}</td>
                <td className="py-3 pr-4 text-gray-500 text-xs">{activity.date}</td>
                <td className="py-3">
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-purple-500 hover:bg-purple-500/10 transition-colors">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-5 flex justify-center">
        <Button 
          variant="ghost" 
          className="group/btn relative px-6 py-2 text-purple-500 hover:text-white hover:bg-transparent overflow-hidden"
        >
          <span className="absolute inset-0 border border-purple-500/50 rounded-md"></span>
          <span className="absolute inset-0 bg-gradient-to-r from-purple-600 to-purple-500 rounded-md opacity-0 group-hover/btn:opacity-100 transition-opacity"></span>
          <span className="relative font-bold tracking-wider">VER TODA LA ACTIVIDAD</span>
        </Button>
      </div>
    </div>
  )
}
