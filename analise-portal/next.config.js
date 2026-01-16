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
};

module.exports = nextConfig;
