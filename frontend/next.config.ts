import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

loadEnvConfig("..", undefined, console, true);

const nextConfig: NextConfig = {
  // Uncomment next line if using Docker
  // output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "image.tmdb.org",
        pathname: "/t/p/w185/*",
        port: "",
        search: "",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: process.env.VERCEL
          ? `https://${process.env.PROD_API_HOST}/:path*`
          : `http://${process.env.LOCAL_API_HOST}:8000/:path*`,
      },
      {
        source: "/openapi.json",
        destination: process.env.VERCEL
          ? `https://${process.env.PROD_API_HOST}/openapi.json`
          : `http://${process.env.LOCAL_API_HOST}:8000/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
