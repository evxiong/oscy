import type { NextConfig } from "next";
import { loadEnvConfig } from "@next/env";

loadEnvConfig("../");

const nextConfig: NextConfig = {
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
        source: "/openapi.json",
        destination:
          process.env.VERCEL_ENV === "production"
            ? "https://oscy-api.vercel.app/openapi.json"
            : "http://localhost:8000/openapi.json",
      },
      {
        source: "/api/:path*",
        destination:
          process.env.VERCEL_ENV === "production"
            ? "https://oscy-api.vercel.app/:path*"
            : "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
