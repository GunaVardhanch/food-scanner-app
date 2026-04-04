/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable static export for Docker deployment with Flask backend
    output: 'export',
    images: {
        unoptimized: true,
    },
    typescript: {
        ignoreBuildErrors: true,
    },
};

export default nextConfig;
