import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';

const nextConfig: NextConfig = {
  output: 'standalone',
};

export default nextConfig;
