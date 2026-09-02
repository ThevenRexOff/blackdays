import { NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 })
  }

  try {
    const { key } = await request.json()

    if (!key || typeof key !== 'string' || !key.trim()) {
      return NextResponse.json({ error: 'La clave de activación es requerida' }, { status: 400 })
    }

    const keyString = key.trim()

    try {
      const result = await prisma.$transaction(async (tx) => {
        // 1. Find user
        const user = await tx.user.findUnique({
          where: { id: session.user.id },
        })

        if (!user) {
          throw new Error('USER_NOT_FOUND')
        }

        if (user.rank === 'baneado') {
          throw new Error('USER_BANNED')
        }

        // 2. Find key
        const dbKey = await tx.key.findUnique({
          where: { key: keyString },
        })

        if (!dbKey || dbKey.isUsed) {
          throw new Error('KEY_INVALID_OR_USED')
        }

        // 3. Calculate new membership expires date
        let newExpiry: Date | null = user.membershipExpiresAt ? new Date(user.membershipExpiresAt) : null
        const now = new Date()

        if (dbKey.days > 0) {
          if (!newExpiry || newExpiry < now) {
            newExpiry = new Date()
            newExpiry.setDate(newExpiry.getDate() + dbKey.days)
          } else {
            newExpiry.setDate(newExpiry.getDate() + dbKey.days)
          }
        }

        // 4. Determine rank (only upgrade user/premium/vip, freeze seller/moderador/admin)
        const upgradeableRanks = ['user', 'premium', 'vip']
        const rankHierarchy: Record<string, number> = { baneado: 0, user: 1, premium: 2, vip: 3, seller: 4, moderador: 5, admin: 6 }
        let newRank = user.rank
        if (upgradeableRanks.includes(user.rank)) {
          const currentLevel = rankHierarchy[user.rank] ?? 0
          const keyLevel = rankHierarchy[dbKey.rank] ?? 0
          if (keyLevel > currentLevel) newRank = dbKey.rank
        }

        // 5. Update user
        const updatedUser = await tx.user.update({
          where: { id: user.id },
          data: {
            credits: { increment: dbKey.credits },
            rank: newRank,
            membershipExpiresAt: newExpiry,
          },
        })

        // 6. Mark key as used
        await tx.key.update({
          where: { id: dbKey.id },
          data: {
            isUsed: true,
            usedById: user.id,
            usedAt: now,
          },
        })

        return {
          creditsAdded: dbKey.credits,
          daysAdded: dbKey.days,
          rankAwarded: dbKey.rank,
          finalCredits: updatedUser.credits,
          finalRank: updatedUser.rank,
          finalExpiry: updatedUser.membershipExpiresAt,
        }
      })

      return NextResponse.json({
        message: 'Clave de activación canjeada exitosamente',
        ...result,
      })
    } catch (txError: any) {
      if (txError.message === 'KEY_INVALID_OR_USED') {
        return NextResponse.json(
          { error: 'La clave de activación es inválida o ya ha sido utilizada' },
          { status: 400 },
        )
      }
      if (txError.message === 'USER_NOT_FOUND') {
        return NextResponse.json(
          { error: 'Usuario no encontrado' },
          { status: 404 },
        )
      }
      if (txError.message === 'USER_BANNED') {
        return NextResponse.json(
          { error: 'Has sido baneado del sistema' },
          { status: 403 },
        )
      }
      throw txError
    }
  } catch (error) {
    console.error('Error redeeming key:', error)
    return NextResponse.json(
      { error: 'Error al canjear la clave de activación' },
      { status: 500 },
    )
  }
}
