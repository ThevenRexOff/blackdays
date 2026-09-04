import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { auth } from '@/lib/auth'

function luhnCheck(pan: string): boolean {
  const digits = pan.replace(/\D/g, '').split('').map(Number)
  if (digits.length < 12) return false
  let sum = 0
  let alt = false
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits[i]
    if (alt) { d *= 2; if (d > 9) d -= 9 }
    sum += d
    alt = !alt
  }
  return sum % 10 === 0
}

function isCardExpired(card: string): boolean {
  const parts = card.split('|')
  if (parts.length < 3) return false
  const month = parseInt(parts[1], 10)
  const year = parseInt(parts[2], 10)
  if (isNaN(month) || isNaN(year)) return false
  if (month < 1 || month > 12) return true
  const fullYear = year < 100 ? 2000 + year : year
  const now = new Date()
  return fullYear < now.getFullYear() || (fullYear === now.getFullYear() && month < now.getMonth() + 1)
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await auth()
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized', status: 'error' }, { status: 401 })
    }

    const { id } = await params
    const body = await request.json()
    const { card, website, email, address, product, cookie, phone, monto } = body as { card: string; website?: string; email?: string; address?: Record<string, unknown> | false; product?: Record<string, unknown> | false; cookie?: string; phone?: string; monto?: string }

    if (!card) {
      return NextResponse.json({ error: 'Card data required', status: 'error' }, { status: 400 })
    }

    const [gate, user] = await Promise.all([
      prisma.gate.findUnique({ where: { id } }),
      prisma.user.findUnique({ where: { id: session.user.id } }),
    ])

    if (!gate) {
      return NextResponse.json({ error: 'Gate not found', status: 'error' }, { status: 404 })
    }

    if (!user) {
      return NextResponse.json({ error: 'User not found', status: 'error' }, { status: 404 })
    }

    if (!gate.isActive && user.rank !== 'admin') {
      return NextResponse.json({
        error: 'Gate deshabilitado',
        status: 'error',
        card: '',
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    if (user.rank === 'baneado') {
      return NextResponse.json({
        error: 'Has sido baneado del sistema',
        status: 'error',
        card: '',
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    if (user.rank === 'user') {
      return NextResponse.json({
        error: 'Membresía expirada — renueva para usar los gates',
        status: 'error',
        card: '',
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    const rankOrder = ['user', 'premium', 'vip', 'seller', 'moderador', 'admin']
    const userRankIndex = rankOrder.indexOf(user.rank)
    const requiredRankIndex = rankOrder.indexOf(gate.minRank)
    if (userRankIndex < 0 || userRankIndex < requiredRankIndex) {
      return NextResponse.json({
        error: 'Rango insuficiente para acceder a este gate',
        status: 'error',
        card: '',
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    const minCost = Math.min(gate.creditsLive, gate.creditsDead)
    if (user.credits < minCost) {
      return NextResponse.json({
        error: 'Credits insuficientes',
        status: 'error',
        card,
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    let resultStatus: 'live' | 'dead' | 'error' = 'error'
    let creditsDeducted = 0
    let phpResponseData: { response?: string; time_taken?: number } = {}

    // ── Server-side card validation ──
    const pan = card.split('|')[0].replace(/\D/g, '')
    if (!luhnCheck(pan) || isCardExpired(card)) {
      return NextResponse.json({
        status: 'dead',
        card,
        response: 'Declined - Invalid Card',
        creditsDeducted: 0,
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    if (!gate.apiUrl) {
      return NextResponse.json({
        error: 'Gate en desarrollo',
        status: 'error',
        code: 'NO_API_URL',
        response: 'Gate en desarrollo — este gate aún no está configurado',
        card,
        creditsRemaining: user.credits,
      }, { status: 200 })
    } else {
      try {
        const phpResponse = await fetch(gate.apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            card,
            website: website || '',
            email: email || '',
            address: address || false,
            product: product || false,
            cookie: cookie || '',
            phone: phone || '',
            monto: monto || '',
          }),
          signal: AbortSignal.timeout(180000), // 3 minutos para evitar timeouts
        })

        if (!phpResponse.ok) {
          return NextResponse.json({ error: 'Gate API error', status: 'error', response: 'Gate API error — verifica la API del gate', card }, { status: 200 })
        }

        const result = await phpResponse.json() as { status?: string | boolean; response?: string; error?: string; code?: string; time_taken?: number; [key: string]: unknown }
        const phpStatus = result.status
        // Normalize backend status to frontend 'live' / 'dead' / 'error'
        if (phpStatus === false || phpStatus === 'error' || (typeof phpStatus === 'string' && phpStatus.toLowerCase().includes('error'))) {
          resultStatus = 'error'
        } else if (phpStatus === 'live' || phpStatus === 'Approved ✅' || phpStatus === 'Live Card 🟢' || phpStatus === 'success') {
          resultStatus = 'live'
        } else {
          resultStatus = 'dead'
        }
        phpResponseData = {
          response: String(result.response ?? result.error ?? '') || (phpStatus === false ? 'Error de la API' : undefined),
          time_taken: result.time_taken,
        }
      } catch {
        return NextResponse.json({ error: 'Gate API timeout', status: 'error', response: 'Gate API timeout — verifica tu conexión', card }, { status: 200 })
      }
    }

    creditsDeducted = resultStatus === 'live' ? gate.creditsLive : gate.creditsDead

    const currentStats = (gate.stats as Record<string, number>) || {}
    const prevLives = currentStats.lives ?? 0
    const prevDeads = currentStats.deads ?? 0
    const prevTotal = currentStats.total ?? 0
    const nextLives = resultStatus === 'live' ? prevLives + 1 : prevLives
    const nextDeads = resultStatus === 'dead' ? prevDeads + 1 : prevDeads
    const nextTotal = prevTotal + 1

    const userUpdate = await prisma.user.updateMany({
      where: { id: user.id, credits: { gte: creditsDeducted } },
      data: {
        credits: { decrement: creditsDeducted },
        ...(resultStatus === 'live' ? { lives: { increment: 1 } } : {}),
        ...(resultStatus === 'dead' ? { deads: { increment: 1 } } : {}),
      },
    })

    if (userUpdate.count === 0) {
      return NextResponse.json({
        error: 'Credits insuficientes para completar la operación',
        status: 'error',
        card,
        creditsRemaining: user.credits,
      }, { status: 200 })
    }

    await prisma.gate.update({
      where: { id: gate.id },
      data: {
        stats: {
          lives: nextLives,
          deads: nextDeads,
          total: nextTotal,
          successRate: Math.round((nextLives / nextTotal) * 100),
        },
      },
    })

    const updatedUser = await prisma.user.findUnique({
      where: { id: user.id },
      select: { credits: true },
    })

    return NextResponse.json({
      status: resultStatus,
      card,
      response: phpResponseData.response,
      time_taken: phpResponseData.time_taken,
      creditsDeducted,
      creditsRemaining: updatedUser?.credits ?? user.credits - creditsDeducted,
    })
  } catch (err) {
    console.error('Gate check error:', err)
    return NextResponse.json({ error: 'Internal error', status: 'error' }, { status: 500 })
  }
}
