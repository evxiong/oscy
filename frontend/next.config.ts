import type { NextConfig } from "next";
import { loadEnvConfig } from "@next/env";

loadEnvConfig("..");

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
};

export default nextConfig;
