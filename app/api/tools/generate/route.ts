import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { auth } from '@/lib/auth'

// Fixed id/pk of the "Amazon Cookie Generator" gate (see prisma/seed.ts).
// Generating a cookie charges the gate's creditsLive, exactly like /check.
export const GENERATOR_GATE_ID = '9a2cf99d-6c22-4d10-8f20-amzgen0001'

export async function POST(request: NextRequest) {
  try {
    const session = await auth()
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized', status: 'error' }, { status: 401 })
    }

    const body = await request.json()
    const { country } = body as { country?: string }
    const ctry = (country || 'US').trim().toUpperCase()
    if (!ctry) {
      return NextResponse.json({ error: 'Missing country', status: 'error' }, { status: 400 })
    }

    const [gate, user] = await Promise.all([
      prisma.gate.findUnique({ where: { id: GENERATOR_GATE_ID } }),
      prisma.user.findUnique({ where: { id: session.user.id } }),
    ])

    if (!gate) {
      return NextResponse.json({ error: 'Generador no configurado (falta fila Gate)', status: 'error', code: 'NO_GENERATOR' }, { status: 404 })
    }
    if (!user) {
      return NextResponse.json({ error: 'User not found', status: 'error' }, { status: 404 })
    }
    if (!gate.apiUrl) {
      return NextResponse.json({ error: 'Generador en desarrollo', status: 'error', code: 'NO_API_URL' }, { status: 200 })
    }

    const rankChecks: Array<[string, string]> = [
      [user.rank === 'baneado' ? 'baneado' : '', 'Has sido baneado del sistema'],
      [user.rank === 'user' ? 'user' : '', 'Membresía expirada — renueva para usar el generador'],
    ]
    for (const [flag, msg] of rankChecks) {
      if (flag) {
        return NextResponse.json({ error: msg, status: 'error', creditsRemaining: user.credits }, { status: 200 })
      }
    }

    if (!gate.isActive && user.rank !== 'admin') {
      return NextResponse.json({ error: 'Gate deshabilitado', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const rankOrder = ['user', 'premium', 'vip', 'seller', 'moderador', 'admin']
    const userRankIndex = rankOrder.indexOf(user.rank)
    const requiredRankIndex = rankOrder.indexOf(gate.minRank)
    if (userRankIndex < 0 || userRankIndex < requiredRankIndex) {
      return NextResponse.json({ error: 'Rango insuficiente para acceder a este gate', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const cost = Math.max(1, gate.creditsLive)
    if (user.credits < cost) {
      return NextResponse.json({ error: 'Credits insuficientes', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    let gen: { status?: boolean | string; cookies?: string; billing?: string; profile?: Record<string, unknown>; country?: string; time_taken?: string; error?: string } | null = null
    try {
      const res = await fetch(gate.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country: ctry }),
        signal: AbortSignal.timeout(180000),
      })
      if (!res.ok) {
        return NextResponse.json({ error: 'Generador API error', status: 'error' }, { status: 200 })
      }
      gen = await res.json() as { status?: boolean | string; cookies?: string; billing?: string; profile?: Record<string, unknown>; country?: string; time_taken?: string; error?: string }
    } catch {
      return NextResponse.json({ error: 'Generador API timeout', status: 'error' }, { status: 200 })
    }

    if (!gen?.status && gen?.error) {
      return NextResponse.json({ error: gen.error, status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }
    if (!gen?.cookies) {
      return NextResponse.json({ error: 'El generador no devolvió cookie', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const deducted = await prisma.user.updateMany({
      where: { id: user.id, credits: { gte: cost } },
      data: { credits: { decrement: cost } },
    })
    if (deducted.count === 0) {
      return NextResponse.json({ error: 'Credits insuficientes para completar la operación', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const currentStats = (gate.stats as Record<string, number>) || {}
    const nextLives = (currentStats.lives ?? 0) + 1
    const nextTotal = (currentStats.total ?? 0) + 1
    await prisma.gate.update({
      where: { id: gate.id },
      data: { stats: { lives: nextLives, deads: currentStats.deads ?? 0, total: nextTotal, successRate: Math.round((nextLives / nextTotal) * 100) } },
    })

    const updated = await prisma.user.findUnique({ where: { id: user.id }, select: { credits: true } })

    return NextResponse.json({
      status: 'live',
      country: gen.country ?? ctry,
      cookies: gen.cookies,
      billing: gen.billing ?? '',
      profile: gen.profile ?? {},
      time_taken: gen.time_taken ?? '',
      creditsDeducted: cost,
      creditsRemaining: updated?.credits ?? user.credits - cost,
    })
  } catch (err) {
    console.error('Generator error:', err)
    return NextResponse.json({ error: 'Internal error', status: 'error' }, { status: 500 })
  }
}
