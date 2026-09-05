import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { auth } from '@/lib/auth'

const GENERATOR_COST = 4 // credits per cookie

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

    const user = await prisma.user.findUnique({ where: { id: session.user.id } })
    if (!user) {
      return NextResponse.json({ error: 'User not found', status: 'error' }, { status: 404 })
    }

    // Rank checks
    if (user.rank === 'baneado') {
      return NextResponse.json({ error: 'Has sido baneado del sistema', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }
    if (user.rank === 'user') {
      return NextResponse.json({ error: 'Membresía expirada — renueva para usar el generador', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const rankOrder = ['user', 'premium', 'vip', 'seller', 'moderador', 'admin']
    const userRankIndex = rankOrder.indexOf(user.rank)
    const requiredRankIndex = rankOrder.indexOf('premium')
    if (userRankIndex < 0 || userRankIndex < requiredRankIndex) {
      return NextResponse.json({ error: 'Rango insuficiente para acceder al generador', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    if (user.credits < GENERATOR_COST) {
      return NextResponse.json({ error: 'Credits insuficientes', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    // Call backend generator
    const backendUrl = 'http://169.58.148.219:8080/apis/amz_generator'
    let gen: { status?: boolean | string; cookies?: string; profile?: Record<string, unknown>; time_taken?: string; error?: string } | null = null
    try {
      const res = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country: ctry }),
        signal: AbortSignal.timeout(300000),
      })
      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`)
      }
      gen = await res.json() as typeof gen
    } catch {
      return NextResponse.json({ error: 'Generador timeout o error', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    if (!gen?.status && gen?.error) {
      return NextResponse.json({ error: gen.error as string, status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }
    if (!gen?.cookies) {
      return NextResponse.json({ error: 'El generador no devolvió cookie', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    // Deduct credits
    const deducted = await prisma.user.updateMany({
      where: { id: user.id, credits: { gte: GENERATOR_COST } },
      data: { credits: { decrement: GENERATOR_COST } },
    })
    if (deducted.count === 0) {
      return NextResponse.json({ error: 'Credits insuficientes', status: 'error', creditsRemaining: user.credits }, { status: 200 })
    }

    const updated = await prisma.user.findUnique({ where: { id: user.id }, select: { credits: true } })

    return NextResponse.json({
      status: 'live',
      country: ctry,
      cookies: gen.cookies,
      profile: gen.profile ?? {},
      time_taken: gen.time_taken ?? '',
      creditsDeducted: GENERATOR_COST,
      creditsRemaining: updated?.credits ?? user.credits - GENERATOR_COST,
    })
  } catch (err) {
    console.error('Amazon cookie generator error:', err)
    return NextResponse.json({ error: 'Internal error', status: 'error' }, { status: 500 })
  }
}
