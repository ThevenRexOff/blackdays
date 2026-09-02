import 'next-auth'

declare module 'next-auth' {
  interface User {
    rank?: string
    membershipExpiresAt?: string | null
  }
  interface Session {
    user: {
      id: string
      name?: string | null
      rank?: string
      membershipExpiresAt?: string | null
    }
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    rank?: string
    membershipExpiresAt?: string | null
  }
}
