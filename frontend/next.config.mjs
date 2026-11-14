/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: the landing page is plain HTML/CSS/JS, deployable to
  // Cloudflare Pages, DeployXA static hosting, or any static host.
  // The waitlist form calls the worker API (NEXT_PUBLIC_API_URL) directly.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
