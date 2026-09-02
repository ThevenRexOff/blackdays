import { auth } from '@/lib/auth'

const managerRanks = ['admin', 'moderador', 'seller']

export async function requireRank(...allowed: string[]) {
  const session = await auth()
  if (!session?.user?.id || !allowed.includes(session.user.rank as string)) {
    return null
  }
  return session
}

export async function requireManager() {
  return requireRank(...managerRanks)
}

export async function requireAdmin() {
  return requireRank('admin')
}

export function isManager(rank: string | null | undefined) {
  return rank ? managerRanks.includes(rank) : false
}

export function isAdmin(rank: string | null | undefined) {
  return rank === 'admin'
}
