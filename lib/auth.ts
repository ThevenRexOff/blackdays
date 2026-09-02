import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers: [
    Credentials({
      name: 'credentials',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null

        const [{ prisma }, bcrypt] = await Promise.all([
          import('@/lib/prisma'),
          import('bcryptjs'),
        ])

        const user = await prisma.user.findUnique({
          where: { username: credentials.username as string },
        })

        if (!user) return null

        const isValid = await bcrypt.compare(
          credentials.password as string,
          user.password,
        )

        if (!isValid) return null

        let rank = user.rank
        const neverExpire = ['admin', 'seller', 'moderador']
        const expired = !user.membershipExpiresAt || new Date(user.membershipExpiresAt) < new Date()
        if (expired && !neverExpire.includes(rank) && rank !== 'baneado') {
          rank = 'user'
          await prisma.user.update({
            where: { id: user.id },
            data: { rank: 'user', credits: 0 },
          })
        }

        return {
          id: user.id,
          name: user.username,
          rank,
          membershipExpiresAt: user.membershipExpiresAt?.toISOString() ?? null,
        }
      },
    }),
  ],
  session: {
    strategy: 'jwt',
  },
  pages: {
    signIn: '/auth/login',
  },
  callbacks: {
    async signIn({ user }) {
      if ((user as Record<string, unknown>).rank === 'baneado') {
        return false
      }
      return true
    },
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
        token.rank = user.rank
        token.membershipExpiresAt = (user as Record<string, unknown>).membershipExpiresAt as string | null ?? null
      }
      return token
    },
    async session({ session, token }) {
      if (session.user && token.id) {
        session.user.id = token.id as string
        session.user.rank = token.rank as string
        session.user.membershipExpiresAt = token.membershipExpiresAt as string | null ?? null
      }
      return session
    },
  },
})
