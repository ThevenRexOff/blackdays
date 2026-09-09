import 'dotenv/config'
import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'

const DATABASE_URL = process.env.DATABASE_URL || ""

const adapter = new PrismaPg({
  connectionString: DATABASE_URL,
})

const prisma = new PrismaClient({ adapter })

function makeStats(lives: number, deads: number): Record<string, number> {
  const total = lives + deads
  return {
    lives,
    deads,
    total,
    successRate: total > 0 ? Math.round((lives / total) * 100) : 0,
  }
}

const BASE = 'http://169.58.148.219:8080/apis'

const newGates = [
  {
    id: 'gate-00000000-nmi-donation-0020',
    name: 'NMI Donation (AIA)',
    category: 'charged',
    description: 'NMI Donation — cargo de donación $16.90 MXN (~$1-5 USD + tarifa).',
    isActive: true,
    apiUrl: `${BASE}/gate/nmi`,
    creditsLive: 20,
    creditsDead: 7,
    minRank: 'premium',
    threads: 1,
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-px-payrix-0021',
    name: 'Payrix GiveDirect',
    category: 'charged',
    description: 'Payrix / GiveDirect — cargo de caridad $5.00.',
    isActive: true,
    apiUrl: `${BASE}/gate/payrix`,
    creditsLive: 20,
    creditsDead: 7,
    minRank: 'premium',
    threads: 1,
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-pz-payezzy-0022',
    name: 'Payeezy Auth',
    category: 'auth',
    description: 'Payeezy (First Data) Auth @ seocontenthero — verificación por añadir método de pago.',
    isActive: true,
    apiUrl: `${BASE}/gate/payezzy`,
    creditsLive: 15,
    creditsDead: 5,
    minRank: 'premium',
    threads: 1,
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-fc-facturas-0023',
    name: 'Telcel Facturas',
    category: 'phone',
    description: 'Telcel Facturas — pago de factura telefónica, requiere número de 10 dígitos.',
    isActive: true,
    apiUrl: `${BASE}/gate/facturas`,
    creditsLive: 15,
    creditsDead: 5,
    minRank: 'premium',
    threads: 1,
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-lv-liverpool-0024',
    name: 'Liverpool Saldo',
    category: 'special',
    description: 'Liverpool — consulta de saldo vía IVR + Twilio (transcripción de audio).',
    isActive: true,
    apiUrl: `${BASE}/gate/liverpool`,
    creditsLive: 10,
    creditsDead: 4,
    minRank: 'premium',
    threads: 1,
    stats: makeStats(0, 0),
  },
]

async function main() {
  for (const gate of newGates) {
    await prisma.gate.upsert({
      where: { id: gate.id },
      update: {
        name: gate.name,
        category: gate.category,
        description: gate.description,
        apiUrl: gate.apiUrl,
        creditsLive: gate.creditsLive,
        creditsDead: gate.creditsDead,
        minRank: gate.minRank,
        threads: gate.threads,
        isActive: gate.isActive,
      },
      create: gate,
    })
    console.log('upserted', gate.id, gate.name)
  }
  const count = await prisma.gate.count()
  console.log('total gates now:', count)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })