import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Self-contained .next/standalone folder (with server.js) for the Docker image
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
