/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // ← REQUIRED for Docker
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
