import { NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

const privilegedRanks = ['admin', 'moderador', 'seller']

async function getSessionUser() {
  const session = await auth()
  if (!session?.user?.id) return null
  return session.user as { id: string; rank: string }
}

async function checkAdmin() {
  const user = await getSessionUser()
  return user?.rank === 'admin'
}

export async function GET() {
  const user = await getSessionUser()
  if (!user || (user.rank !== 'admin' && user.rank !== 'moderador')) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  const users = await prisma.user.findMany({
    orderBy: { createdAt: 'desc' },
    select: {
      id: true,
      username: true,
      telegramId: true,
      rank: true,
      credits: true,
      lives: true,
      deads: true,
      membershipExpiresAt: true,
      createdAt: true,
    },
  })

  return NextResponse.json(users)
}

export async function POST(request: Request) {
  if (!(await checkAdmin())) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const bcrypt = await import('bcryptjs')
    const hashedPassword = await bcrypt.hash(body.password || '123456', 10)

    const user = await prisma.user.create({
      data: {
        username: body.username,
        password: hashedPassword,
        telegramId: body.telegramId || '',
        rank: body.rank || 'user',
        credits: body.credits ?? 0,
        membershipExpiresAt: body.membershipExpiresAt ? new Date(body.membershipExpiresAt) : null,
      },
      select: {
        id: true,
        username: true,
        telegramId: true,
        rank: true,
        credits: true,
        lives: true,
        deads: true,
        membershipExpiresAt: true,
        createdAt: true,
      },
    })
    return NextResponse.json(user)
  } catch {
    return NextResponse.json({ error: 'Error al crear usuario' }, { status: 500 })
  }
}

export async function DELETE(request: Request) {
  if (!(await checkAdmin())) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const { id } = await request.json()
    if (!id) {
      return NextResponse.json({ error: 'ID requerido' }, { status: 400 })
    }
    await prisma.user.delete({ where: { id } })
    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json({ error: 'Error al eliminar usuario' }, { status: 500 })
  }
}

export async function PATCH(request: Request) {
  const user = await getSessionUser()
  if (!user || (user.rank !== 'admin' && user.rank !== 'moderador')) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const { id, credits, rank, membershipExpiresAt } = await request.json()
    if (!id) {
      return NextResponse.json({ error: 'ID requerido' }, { status: 400 })
    }

    const target = await prisma.user.findUnique({ where: { id } })
    if (!target) {
      return NextResponse.json({ error: 'Usuario no encontrado' }, { status: 404 })
    }

    if (user.rank !== 'admin' && privilegedRanks.includes(target.rank)) {
      return NextResponse.json({ error: 'No puedes editar usuarios privilegiados' }, { status: 403 })
    }

    if (rank !== undefined && user.rank !== 'admin' && privilegedRanks.includes(rank)) {
      return NextResponse.json({ error: 'No puedes asignar un rango privilegiado' }, { status: 403 })
    }

    const data: Record<string, unknown> = {}
    if (credits !== undefined) data.credits = credits
    if (rank !== undefined) data.rank = rank
    if (membershipExpiresAt !== undefined) {
      data.membershipExpiresAt = membershipExpiresAt ? new Date(membershipExpiresAt) : null
    }

    const updated = await prisma.user.update({
      where: { id },
      data,
      select: {
        id: true,
        username: true,
        telegramId: true,
        rank: true,
        credits: true,
        lives: true,
        deads: true,
        membershipExpiresAt: true,
        createdAt: true,
      },
    })

    return NextResponse.json(updated)
  } catch {
    return NextResponse.json({ error: 'Error al actualizar usuario' }, { status: 500 })
  }
}
