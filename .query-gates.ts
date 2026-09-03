import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'
import fs from 'fs'

const envFile = fs.readFileSync('.env', 'utf8')
const m = envFile.match(/DATABASE_URL="([^"]+)"/)
const DATABASE_URL = m ? m[1] : ''

const adapter = new PrismaPg({ connectionString: DATABASE_URL })
const prisma = new PrismaClient({ adapter })

async function main() {
  const gates = await prisma.gate.findMany({ orderBy: { createdAt: 'asc' } })
  console.log('TOTAL GATES:', gates.length)
  for (const g of gates) {
    console.log(JSON.stringify({
      id: g.id, name: g.name, category: g.category, isActive: g.isActive,
      apiUrl: g.apiUrl, creditsLive: g.creditsLive, creditsDead: g.creditsDead,
      minRank: g.minRank, threads: g.threads,
    }))
  }
}

main()
  .catch((e) => { console.error('ERROR:', e.message); process.exit(1) })
  .finally(() => prisma.$disconnect())
