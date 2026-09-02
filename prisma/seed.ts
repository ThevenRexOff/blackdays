import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'

const DATABASE_URL = process.env.DATABASE_URL || "postgres://postgres:postgres@localhost:51214/template1?sslmode=disable&connection_limit=10&connect_timeout=0&max_idle_connection_lifetime=0&pool_timeout=0&socket_timeout=0"

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

// const rankOrder = ['premium', 'vip', 'seller', 'moderador', 'admin']

const gates = [
  {
    id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    name: 'Auth Gate Alpha',
    category: 'auth',
    description: 'Puerta de autenticación principal para verificación de acceso seguro',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 15,
    creditsDead: 5,
    minRank: 'premium',
    stats: makeStats(342, 58),
  },
  {
    id: '3b018596-3b98-4228-9844-38c82ef9ebaa',
    name: 'Auth Gate Beta',
    category: 'auth',
    description: 'Puerta de autenticación secundaria para verificación de respaldo',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 20,
    creditsDead: 10,
    minRank: 'premium',
    stats: makeStats(187, 43),
  },
  {
    id: 'c93f0b22-8610-449e-af54-47f98d793617',
    name: 'Charged Gate Pro',
    category: 'charged',
    description: 'Puerta premium con capacidades de verificación avanzadas',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 35,
    creditsDead: 15,
    minRank: 'vip',
    stats: makeStats(512, 120),
  },
  {
    id: '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
    name: 'Charged Gate Elite',
    category: 'charged',
    description: 'Puerta de nivel elite para usuarios con mayor volumen',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 50,
    creditsDead: 20,
    minRank: 'seller',
    stats: makeStats(890, 210),
  },
  {
    id: '6b29fc40-247a-4cd8-8924-f1ce68545939',
    name: 'CCN Gate Ultra',
    category: 'ccn',
    description: 'Puerta de alta seguridad para operaciones de verificación de tarjetas',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 60,
    creditsDead: 30,
    minRank: 'seller',
    stats: makeStats(1234, 345),
  },
  {
    id: '4e9b9426-8968-466a-a07c-9b81f1d11b22',
    name: 'CCN Gate Max',
    category: 'ccn',
    description: 'Puerta CCN con máximo rendimiento y baja tasa de error',
    isActive: false,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 80,
    creditsDead: 40,
    minRank: 'moderador',
    stats: makeStats(0, 0),
  },
  {
    id: 'a91176b5-0557-41eb-883a-441113b2ab68',
    name: 'Special Gate One',
    category: 'special',
    description: 'Puerta exclusiva con algoritmos de verificación únicos',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 120,
    creditsDead: 50,
    minRank: 'moderador',
    stats: makeStats(67, 23),
  },
  {
    id: '7b018596-3b98-4228-9844-38c82ef9ebaa',
    name: 'Special Gate Phantom',
    category: 'special',
    description: 'Puerta especial con modo fantasma para verificaciones sigilosas',
    isActive: false,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 200,
    creditsDead: 100,
    minRank: 'admin',
    stats: makeStats(0, 0),
  },
  {
    id: '8c918596-3b98-4228-9844-38c82ef9ebaa',
    name: 'Shopify Checkout',
    category: 'shopify',
    description: 'Puerta especializada para checkouts de Shopify',
    isActive: true,
    apiUrl: 'http://localhost:9000/php/api.php',
    creditsLive: 40,
    creditsDead: 10,
    minRank: 'premium',
    stats: makeStats(256, 89),
  },
]

async function main() {
  console.log('Seeding gates...')

  await prisma.gate.deleteMany()

  for (const gate of gates) {
    await prisma.gate.upsert({
      where: { id: gate.id },
      update: {},
      create: gate,
    })
  }

  console.log(`Seeded ${gates.length} gates`)

  console.log('Seeding users...')

  const bcrypt = await import('bcryptjs')
  const hashedPassword = await bcrypt.hash('dfbc1992', 10)

  const pastDate = new Date('2024-01-01')
  const futureDate = new Date('2030-01-01')

  const seedUsers = [
    { username: 'thevenrex', password: hashedPassword, telegramId: '000000000', rank: 'admin' as const, credits: 9999, lives: 45, deads: 12, membershipExpiresAt: futureDate },
    { username: 'd4rk_b1t', password: hashedPassword, telegramId: '555555555', rank: 'seller' as const, credits: 4100, lives: 312, deads: 78, membershipExpiresAt: futureDate },
    { username: 'cipher_zero', password: hashedPassword, telegramId: '333333333', rank: 'moderador' as const, credits: 3200, lives: 210, deads: 55, membershipExpiresAt: futureDate },
    { username: 'neo42', password: hashedPassword, telegramId: '111111111', rank: 'vip' as const, credits: 2500, lives: 128, deads: 34, membershipExpiresAt: futureDate },
    { username: 'h4ck3r_01', password: hashedPassword, telegramId: '222222222', rank: 'user' as const, credits: 1800, lives: 89, deads: 27, membershipExpiresAt: pastDate },
    { username: 'ph4nt0m', password: hashedPassword, telegramId: '444444444', rank: 'user' as const, credits: 750, lives: 34, deads: 18, membershipExpiresAt: pastDate },
    { username: 'baneado_user', password: hashedPassword, telegramId: '666666666', rank: 'baneado' as const, credits: 0, lives: 0, deads: 0, membershipExpiresAt: null },
  ]

  for (const user of seedUsers) {
    const { membershipExpiresAt, ...rest } = user
    await prisma.user.upsert({
      where: { username: user.username },
      update: { lives: user.lives, deads: user.deads },
      create: { ...rest, membershipExpiresAt },
    })
  }

  console.log(`Seeded ${seedUsers.length} users (password: dfbc1992)`)
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
