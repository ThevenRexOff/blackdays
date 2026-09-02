import { NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

export async function GET() {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 })
  }

  const [gates, users, profile] = await Promise.all([
    prisma.gate.findMany({ orderBy: { createdAt: 'desc' } }),
    prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        username: true,
        rank: true,
        credits: true,
        lives: true,
        deads: true,
        createdAt: true,
      },
    }),
    prisma.user.findUnique({
      where: { id: session.user.id },
      select: { credits: true, telegramId: true, rank: true, createdAt: true },
    }),
  ])

  const totalLives = gates.reduce((s, g) => s + ((g.stats as Record<string, number>)?.lives ?? 0), 0)
  const totalDeads = gates.reduce((s, g) => s + ((g.stats as Record<string, number>)?.deads ?? 0), 0)

  const catMap = new Map<string, { count: number; lives: number; deads: number }>()
  for (const g of gates) {
    const stats = g.stats as Record<string, number> | null
    const c = catMap.get(g.category) ?? { count: 0, lives: 0, deads: 0 }
    c.count++
    c.lives += stats?.lives ?? 0
    c.deads += stats?.deads ?? 0
    catMap.set(g.category, c)
  }

  const topGates = [...gates]
    .filter(g => ((g.stats as Record<string, number>)?.lives ?? 0) + ((g.stats as Record<string, number>)?.deads ?? 0) > 0)
    .sort((a, b) => ((b.stats as Record<string, number>)?.lives ?? 0) - ((a.stats as Record<string, number>)?.lives ?? 0))
    .slice(0, 5)
    .map(g => ({
      name: g.name,
      lives: (g.stats as Record<string, number>)?.lives ?? 0,
      deads: (g.stats as Record<string, number>)?.deads ?? 0,
      successRate: (g.stats as Record<string, number>)?.successRate ?? 0,
    }))

  const topUsers = [...users]
    .filter(u => (u.lives ?? 0) + (u.deads ?? 0) > 0)
    .sort((a, b) => (b.lives ?? 0) - (a.lives ?? 0))
    .slice(0, 5)
    .map(u => ({ username: u.username, lives: u.lives ?? 0, deads: u.deads ?? 0, rank: u.rank ?? 'user' }))

  const recentUsers = users.slice(0, 5).map(u => ({ username: u.username, createdAt: u.createdAt }))

  const recentGates = gates.slice(0, 5).map(g => ({ name: g.name, category: g.category, createdAt: g.createdAt }))

  return NextResponse.json({
    userCount: users.length,
    gateCount: gates.length,
    activeGateCount: gates.filter(g => g.isActive).length,
    totalLives,
    totalDeads,
    topGates,
    topUsers,
    recentUsers,
    recentGates,
    gatesByCategory: [...catMap.entries()].map(([category, v]) => ({ category, ...v })),
    userCredits: profile?.credits ?? 0,
    userTelegram: profile?.telegramId ?? '—',
    userRank: profile?.rank ?? session.user.rank ?? 'user',
    userCreated: profile?.createdAt?.toISOString() ?? '',
  })
}
