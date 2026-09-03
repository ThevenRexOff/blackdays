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

const BASE = 'http://169.58.148.219:8080/apis'

const gates = [
  {
    id: 'gate-00000000-mj-stripe-auth-0001',
    name: 'MJ Stripe Auth',
    category: 'auth',
    description: 'Stripe Auth gate — verificación de tarjeta por cargo de autorización.',
    isActive: true,
    apiUrl: `${BASE}/gate/mj`,
    creditsLive: 15,
    creditsDead: 5,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-mm-moscow-mule-0002',
    name: 'MM Moscow Mule',
    category: 'charged',
    description: 'Authorize.Net Cargo $2 — puerta de cargo cobrado.',
    isActive: true,
    apiUrl: `${BASE}/gate/mm`,
    creditsLive: 20,
    creditsDead: 8,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-wr-white-russian-0003',
    name: 'WR White Russian',
    category: 'ccn',
    description: 'Recurly CCN cargado $12 — puerta de CCN con cargo recurrente.',
    isActive: true,
    apiUrl: `${BASE}/gate/wr`,
    creditsLive: 25,
    creditsDead: 10,
    minRank: 'vip',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-br-battle-0004',
    name: 'BR Battle.net',
    category: 'charged',
    description: 'Blizzard / Battle.net gate (núcleo Disney+) — cargo de verificación.',
    isActive: true,
    apiUrl: `${BASE}/gate/br`,
    creditsLive: 18,
    creditsDead: 6,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-bl-blizzard-0005',
    name: 'BL Blizzard',
    category: 'charged',
    description: 'Blizzard / Battle.net (núcleo Disney+) con proxy MX.',
    isActive: true,
    apiUrl: `${BASE}/gate/bl`,
    creditsLive: 18,
    creditsDead: 6,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-dns-dns-0006',
    name: 'DNS Gate',
    category: 'auth',
    description: 'Puerta DNS de autenticación de tarjeta.',
    isActive: true,
    apiUrl: `${BASE}/gate/dns`,
    creditsLive: 12,
    creditsDead: 4,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-rc-rc-0007',
    name: 'RC Gate',
    category: 'ccn',
    description: 'Puerta RC de verificación de CCN.',
    isActive: true,
    apiUrl: `${BASE}/gate/rc`,
    creditsLive: 14,
    creditsDead: 5,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-op-op-0008',
    name: 'OP Gate',
    category: 'ccn',
    description: 'Puerta OP de verificación de CCN (OpenPay).',
    isActive: true,
    apiUrl: `${BASE}/gate/op`,
    creditsLive: 14,
    creditsDead: 5,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-pd-playdoit-0009',
    name: 'PD PlayDoit MX',
    category: 'ccn',
    description: 'PlayDoit MX CCN — Depósito $100, con proxy MX.',
    isActive: true,
    apiUrl: `${BASE}/gate/pd`,
    creditsLive: 30,
    creditsDead: 12,
    minRank: 'vip',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-wu-wu-0010',
    name: 'WU Gate',
    category: 'charged',
    description: 'Puerta WU de cargo de verificación.',
    isActive: true,
    apiUrl: `${BASE}/gate/wu`,
    creditsLive: 16,
    creditsDead: 6,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-zb-telcel-0011',
    name: 'ZB Telcel ClaroPay',
    category: 'phone',
    description: 'Telcel ClaroPay — recargas, requiere teléfono y monto.',
    isActive: true,
    apiUrl: `${BASE}/gate/zb`,
    creditsLive: 10,
    creditsDead: 3,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-ps-bait-0012',
    name: 'PS BAIT Recargas',
    category: 'phone',
    description: 'BAIT recargas — requiere teléfono y monto, con proxy MX.',
    isActive: true,
    apiUrl: `${BASE}/gate/ps`,
    creditsLive: 10,
    creditsDead: 3,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: '8c918596-3b98-4228-9844-38c82ef9ebaa',
    name: 'Shopify Checkout',
    category: 'shopify',
    description: 'Shopify Checkout — requiere website (tienda de Shopify).',
    isActive: true,
    apiUrl: `${BASE}/gate/shopify`,
    creditsLive: 40,
    creditsDead: 10,
    minRank: 'premium',
    stats: makeStats(256, 89),
  },
  {
    id: 'gate-00000000-amz-amazon-0014',
    name: 'Amazon (Cookie)',
    category: 'special',
    description: 'Amazon — requiere cookie de Amazon.',
    isActive: true,
    apiUrl: `${BASE}/gate/amz`,
    creditsLive: 22,
    creditsDead: 8,
    minRank: 'vip',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-nfx-netflix-0015',
    name: 'Netflix Plans MX',
    category: 'special',
    description: 'Netflix Plans MX — requiere CAPSOLVER_KEY.',
    isActive: true,
    apiUrl: `${BASE}/gate/netflix`,
    creditsLive: 35,
    creditsDead: 12,
    minRank: 'vip',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-dsy-disney-0016',
    name: 'Disney+ Plans MX',
    category: 'special',
    description: 'Disney+ Plans MX — requiere CAPSOLVER_KEY.',
    isActive: true,
    apiUrl: `${BASE}/gate/disney`,
    creditsLive: 35,
    creditsDead: 12,
    minRank: 'vip',
    stats: makeStats(0, 0),
  },
  {
    id: 'gate-00000000-tcl-telcel-0017',
    name: 'Telcel MX Recargas',
    category: 'phone',
    description: 'Telcel MX recharges — requiere teléfono y monto.',
    isActive: true,
    apiUrl: `${BASE}/gate/telcel`,
    creditsLive: 10,
    creditsDead: 3,
    minRank: 'premium',
    stats: makeStats(0, 0),
  },
  {
    id: '9a2cf99d-6c22-4d10-8f20-amzgen0001',
    name: 'Amazon Cookie Generator',
    category: 'cookie',
    description: 'Genera una cookie de Amazon (US) — cobra créditos por generación. BIN/card no aplica.',
    isActive: true,
    apiUrl: `${BASE}/amz_generator`,
    creditsLive: 25,
    creditsDead: 0,
    minRank: 'premium',
    stats: makeStats(0, 0),
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
