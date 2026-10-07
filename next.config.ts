import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static HTML for Netlify CDN. Avoids publishing `.next` as a broken static site.
  output: "export",
  trailingSlash: true,
  poweredByHeader: false,
  compress: true,
  images: {
    unoptimized: true,
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
