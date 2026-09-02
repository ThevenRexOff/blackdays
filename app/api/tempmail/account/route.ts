import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

const ALLOWED_RANKS = ['user', 'premium', 'vip', 'moderador', 'seller', 'admin']

export async function GET() {
  const session = await auth()
  if (!session?.user?.id || !session?.user?.rank || !ALLOWED_RANKS.includes(session.user.rank as string)) {
    return NextResponse.json({ error: 'Acceso denegado' }, { status: 403 })
  }

  const account = await prisma.tempMail.findFirst({
    where: { userId: session.user.id as string },
    orderBy: { createdAt: 'desc' },
  })

  return NextResponse.json({ account })
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user?.id || !session?.user?.rank || !ALLOWED_RANKS.includes(session.user.rank as string)) {
    return NextResponse.json({ error: 'Acceso denegado' }, { status: 403 })
  }

  const body = await req.json()
  const { service, email, type, token, password, domain, sidToken, dropToken, sessionId } = body

  if (!service || !email || !type) {
    return NextResponse.json({ error: 'Faltan campos requeridos' }, { status: 400 })
  }

  // Delete old account for this user first
  await prisma.tempMail.deleteMany({
    where: { userId: session.user.id as string },
  })

  const account = await prisma.tempMail.create({
    data: {
      userId: session.user.id as string,
      service,
      email,
      type,
      token,
      password,
      domain,
      sidToken,
      dropToken,
      sessionId,
    },
  })

  return NextResponse.json({ account })
}

export async function DELETE() {
  const session = await auth()
  if (!session?.user?.id || !session?.user?.rank || !ALLOWED_RANKS.includes(session.user.rank as string)) {
    return NextResponse.json({ error: 'Acceso denegado' }, { status: 403 })
  }

  await prisma.tempMail.deleteMany({
    where: { userId: session.user.id as string },
  })

  return NextResponse.json({ success: true })
}
