import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // React Configuration
  reactStrictMode: true,
  
  // Performance Optimizations
  compress: true,
  
  // Image Optimization
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60,
  },
  
  // Environment Variables
  env: {
    APP_NAME: 'Smart Care Shield',
    APP_VERSION: '2.0.0',
  },
  
  // Headers for Security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
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
  
  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },
  
  // Webpack Configuration
  webpack: (config, { isServer }) => {
    // Custom webpack config here
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
  
  // Experimental Features
  experimental: {
    optimizePackageImports: ['@mui/material', '@mui/icons-material'],
  },
  
  // Turbopack Configuration
  turbopack: {},
  
  // Output Configuration
  output: 'standalone',
  
  // TypeScript
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
