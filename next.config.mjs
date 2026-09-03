/** @type {import('next').NextConfig} */
const allowedOrigins = (process.env.CORS_ORIGINS || 'https://www.jillchk.com').split(',').map(s => s.trim()).filter(Boolean)

const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  serverExternalPackages: ['@prisma/adapter-pg', 'pg', 'bcryptjs'],
  allowedDevOrigins: ['192.168.1.8', '23f9-2803-6320-2a-6bdc-2407-5724-c8f6-55e0.ngrok-free.app'],
  async headers() {
    return [{
      source: '/api/:path*',
      headers: [
        { key: 'Access-Control-Allow-Origin', value: allowedOrigins[0] || 'https://www.jillchk.com' },
        { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,PATCH,DELETE,OPTIONS' },
        { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        { key: 'Access-Control-Allow-Credentials', value: 'true' },
      ],
    }]
  },
}

export default nextConfig
