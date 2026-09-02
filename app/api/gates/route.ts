import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET() {
  try {
    const gates = await prisma.gate.findMany({
      orderBy: { createdAt: 'desc' },
    })
    return NextResponse.json(gates)
  } catch (error) {
    console.error('Error fetching gates:', error)
    return NextResponse.json([], { status: 500 })
  }
}
