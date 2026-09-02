import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params
    const gate = await prisma.gate.findUnique({
      where: { id },
    })

    if (!gate) {
      return NextResponse.json(
        { error: 'Gate not found' },
        { status: 404 },
      )
    }

    return NextResponse.json(gate)
  } catch (error) {
    console.error('Error fetching gate:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 },
    )
  }
}
