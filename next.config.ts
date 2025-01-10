import type { NextConfig } from "next";

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
  /* config options here */
};

export default nextConfig;
