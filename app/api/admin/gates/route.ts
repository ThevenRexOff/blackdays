import { NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

async function checkAdmin() {
  const session = await auth()
  if (!session?.user?.id || session.user.rank !== 'admin') {
    return false
  }
  return true
}

export async function GET() {
  if (!(await checkAdmin())) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  const gates = await prisma.gate.findMany({
    orderBy: { createdAt: 'desc' },
  })

  const stats = await prisma.gate.aggregate({
    _sum: { creditsLive: true, creditsDead: true },
    _count: true,
  })

  return NextResponse.json({
    gates,
    totalGates: stats._count,
    totalCreditsLive: stats._sum.creditsLive ?? 0,
    totalCreditsDead: stats._sum.creditsDead ?? 0,
  })
}

export async function POST(request: Request) {
  if (!(await checkAdmin())) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const gate = await prisma.gate.create({
      data: {
        name: body.name || 'Nuevo Gate',
        category: body.category || 'auth',
        description: body.description || '',
        apiUrl: body.apiUrl || '',
        creditsLive: body.creditsLive ?? 0,
        creditsDead: body.creditsDead ?? 0,
        minRank: body.minRank || 'premium',
        threads: body.threads ?? 1,
        isActive: body.isActive ?? true,
      },
    })
    return NextResponse.json(gate)
  } catch {
    return NextResponse.json({ error: 'Error al crear gate' }, { status: 500 })
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
    await prisma.gate.delete({ where: { id } })
    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json({ error: 'Error al eliminar gate' }, { status: 500 })
  }
}

export async function PATCH(request: Request) {
  if (!(await checkAdmin())) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
  }

  try {
    const { id, ...data } = await request.json()
    if (!id) {
      return NextResponse.json({ error: 'ID requerido' }, { status: 400 })
    }

    const gate = await prisma.gate.update({
      where: { id },
      data,
    })

    return NextResponse.json(gate)
  } catch {
    return NextResponse.json({ error: 'Error al actualizar gate' }, { status: 500 })
  }
}
