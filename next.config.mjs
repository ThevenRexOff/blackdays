/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  serverExternalPackages: ['@prisma/adapter-pg', 'pg', 'bcryptjs'],
  allowedDevOrigins: ['192.168.1.8', '23f9-2803-6320-2a-6bdc-2407-5724-c8f6-55e0.ngrok-free.app'],
}

export default nextConfig
