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
        source: "/api/revalidate",
        destination: "/api/revalidate",
      },
      {
        source: "/api/:path*",
        destination:
          process.env.VERCEL_ENV === "production"
            ? "https://oscy-api.vercel.app/:path*"
            : `http://${process.env.API_HOST}:8000/:path*`,
      },
      {
        source: "/openapi.json",
        destination:
          process.env.VERCEL_ENV === "production"
            ? "https://oscy-api.vercel.app/openapi.json"
            : `http://${process.env.API_HOST}:8000/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
