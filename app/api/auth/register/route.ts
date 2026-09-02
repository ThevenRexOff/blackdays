import { NextRequest, NextResponse } from 'next/server'
import bcrypt from 'bcryptjs'
import { prisma } from '@/lib/prisma'

export async function POST(request: NextRequest) {
  try {
    const { username, password, telegramId, key } = await request.json()

    if (!username || !password || !telegramId || !key) {
      return NextResponse.json(
        { error: 'Usuario, contraseña, ID de Telegram y clave de activación son requeridos' },
        { status: 400 },
      )
    }

    const existingUser = await prisma.user.findUnique({
      where: { username },
    })

    if (existingUser) {
      return NextResponse.json(
        { error: 'El usuario ya está registrado' },
        { status: 400 },
      )
    }

    try {
      const user = await prisma.$transaction(async (tx) => {
        const dbKey = await tx.key.findUnique({
          where: { key: key.trim() },
        })

        if (!dbKey || dbKey.isUsed) {
          throw new Error('KEY_INVALID_OR_USED')
        }

        const hashedPassword = await bcrypt.hash(password, 12)

        let membershipExpiresAt: Date | null = null
        if (dbKey.days > 0) {
          membershipExpiresAt = new Date()
          membershipExpiresAt.setDate(membershipExpiresAt.getDate() + dbKey.days)
        }

        const newUser = await tx.user.create({
          data: {
            username,
            password: hashedPassword,
            telegramId,
            credits: dbKey.credits,
            rank: dbKey.rank || 'premium',
            membershipExpiresAt,
          },
        })

        await tx.key.update({
          where: { id: dbKey.id },
          data: {
            isUsed: true,
            usedById: newUser.id,
            usedAt: new Date(),
          },
        })

        return newUser
      })

      return NextResponse.json(
        { message: 'Usuario creado exitosamente', userId: user.id },
        { status: 201 },
      )
    } catch (txError: any) {
      if (txError.message === 'KEY_INVALID_OR_USED') {
        return NextResponse.json(
          { error: 'La clave de activación es inválida o ya ha sido utilizada' },
          { status: 400 },
        )
      }
      throw txError
    }
  } catch (error) {
    console.error('Error creating user:', error)
    return NextResponse.json(
      { error: 'Error al crear el usuario' },
      { status: 500 },
    )
  }
}
