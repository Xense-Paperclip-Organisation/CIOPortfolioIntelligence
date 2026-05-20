/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverComponentsExternalPackages: ['puppeteer']
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'logo.clearbit.com' },
      { protocol: 'https', hostname: 'companieslogo.com' }
    ]
  },
  async rewrites() {
    const backend = process.env.BACKEND_URL || 'http://backend:8000';
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` }
    ];
  }
};
export default nextConfig;
