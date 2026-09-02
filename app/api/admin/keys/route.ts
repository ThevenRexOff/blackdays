import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { requireManager } from '@/lib/auth-helpers'

function generateActivationKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  const segment = () => Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
  return `TRBL-${segment()}-${segment()}-${segment()}`
}

const privilegedRanks = ['admin', 'moderador', 'seller']

export async function GET() {
  const session = await requireManager()
  if (!session) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const where =
      session.user.rank === 'admin'
        ? {}
        : { rank: { notIn: privilegedRanks } }

    const keys = await prisma.key.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      include: {
        usedBy: {
          select: { username: true },
        },
        createdBy: {
          select: { username: true },
        },
      },
    })
    return NextResponse.json(keys)
  } catch (error) {
    console.error('Error fetching keys:', error)
    return NextResponse.json({ error: 'Error al obtener las claves' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  const session = await requireManager()
  if (!session) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const credits = Number(body.credits ?? 0)
    const days = Number(body.days ?? 0)
    let rank = body.rank || 'user'
    const count = Math.min(Math.max(Number(body.count ?? 1), 1), 50)

    if (session.user.rank !== 'admin' && privilegedRanks.includes(rank)) {
      rank = 'user'
    }

    const createdKeys = []

    for (let i = 0; i < count; i++) {
      let uniqueKey = generateActivationKey()
      let attempts = 0
      let success = false

      while (attempts < 10 && !success) {
        try {
          const newKey = await prisma.key.create({
            data: {
              key: uniqueKey,
              credits,
              days,
              rank,
              createdById: session.user.id,
            },
          })
          createdKeys.push(newKey)
          success = true
        } catch (err: any) {
          if (err.code === 'P2002') {
            uniqueKey = generateActivationKey()
            attempts++
          } else {
            throw err
          }
        }
      }

      if (!success) {
        throw new Error('No se pudo generar una clave única después de varios intentos')
      }
    }

    return NextResponse.json(createdKeys)
  } catch (error) {
    console.error('Error generating keys:', error)
    return NextResponse.json({ error: 'Error al generar claves' }, { status: 500 })
  }
}

export async function PATCH(request: Request) {
  const session = await requireManager()
  if (!session) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const { id, credits, days, rank } = await request.json()
    if (!id) {
      return NextResponse.json({ error: 'ID requerido' }, { status: 400 })
    }

    const dbKey = await prisma.key.findUnique({ where: { id } })
    if (!dbKey) {
      return NextResponse.json({ error: 'Clave no encontrada' }, { status: 404 })
    }

    if (dbKey.isUsed) {
      return NextResponse.json({ error: 'No se puede editar una clave que ya ha sido utilizada' }, { status: 400 })
    }

    if (rank !== undefined && session.user.rank !== 'admin' && privilegedRanks.includes(rank)) {
      return NextResponse.json({ error: 'No puedes asignar un rango privilegiado' }, { status: 403 })
    }

    const data: Record<string, unknown> = {}
    if (credits !== undefined) data.credits = credits
    if (days !== undefined) data.days = days
    if (rank !== undefined) data.rank = rank

    const updated = await prisma.key.update({
      where: { id },
      data,
    })

    return NextResponse.json(updated)
  } catch (error) {
    console.error('Error updating key:', error)
    return NextResponse.json({ error: 'Error al actualizar la clave' }, { status: 500 })
  }
}

export async function DELETE(request: Request) {
  const session = await requireManager()
  if (!session) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const { id } = await request.json()
    if (!id) {
      return NextResponse.json({ error: 'ID requerido' }, { status: 400 })
    }

    const dbKey = await prisma.key.findUnique({ where: { id } })
    if (!dbKey) {
      return NextResponse.json({ error: 'Clave no encontrada' }, { status: 404 })
    }

    if (dbKey.isUsed) {
      return NextResponse.json({ error: 'No se puede eliminar una clave que ya ha sido utilizada' }, { status: 400 })
    }

    await prisma.key.delete({ where: { id } })
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting key:', error)
    return NextResponse.json({ error: 'Error al eliminar la clave' }, { status: 500 })
  }
}
