/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    // Desabilitar verificação de tipos durante o build (temporário)
    ignoreBuildErrors: true,
  },
  eslint: {
    // Desabilitar verificação de lint durante o build (temporário)
    ignoreDuringBuilds: true,
  },
  // Limitar workers para hospedagem compartilhada
  experimental: {
    workerThreads: false,
    cpus: 1,
  },
  // Configurações de segurança e headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
