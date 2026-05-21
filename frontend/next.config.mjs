/** @type {import('next').NextConfig} */
// PUBLIC_PROXY_PREFIX is the path prefix the Paperclip plugin static proxy
// adds when serving this Next.js app via https://www.xense.dev/_plugins/<key>/ui/...
// Setting assetPrefix to this prefix makes Next.js emit asset URLs (/_next/...)
// that round-trip back through the proxy. The proxy strips the prefix before
// fetching upstream, so the local server (127.0.0.1:3000) remains prefix-free.
const PUBLIC_PROXY_PREFIX = process.env.NEXT_PUBLIC_PROXY_PREFIX || '';

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
  ...(PUBLIC_PROXY_PREFIX ? { assetPrefix: PUBLIC_PROXY_PREFIX } : {}),
  async rewrites() {
    const backend = process.env.BACKEND_URL || 'http://backend:8000';
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` }
    ];
  }
};
export default nextConfig;
