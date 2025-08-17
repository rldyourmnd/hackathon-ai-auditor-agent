/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  trailingSlash: false,
  swcMinify: true,
  poweredByHeader: false,
  compress: true,
  images: {
    unoptimized: true
  }
}

module.exports = nextConfig
