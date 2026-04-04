/** @type {import('next').NextConfig} */
const nextConfig = {
    // Removed 'output: export' to use standard Next.js server mode with npm run dev
    // Static export is only needed for static hosting (Vercel, Netlify static sites)
    images: {
        unoptimized: true,
    },
    typescript: {
        ignoreBuildErrors: true,
    },
};

export default nextConfig;
