/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                // Premium Design System - Golden Yellow Accent
                accent: '#ffd624',
                'accent-dark': '#f59e1b',
                'accent-light': '#ffd624',
                
                // Legacy Aahar AI palette (kept for backwards compatibility)
                saffron: '#FF9933',
                'india-green': '#138808',
                'ashoka-blue': '#000080',
                'dark-navy': '#0D0D2B',
                'warm-cream': '#FFF8F0',
                
                // Semantic colors
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444',
                info: '#3b82f6',
                
                // Neutral palette
                slate: {
                    50: '#f9fafb',
                    100: '#f3f4f6',
                    200: '#e5e7eb',
                    300: '#d1d5db',
                    400: '#9ca3af',
                    500: '#6b7280',
                    600: '#4b5563',
                    700: '#374151',
                    800: '#1f2937',
                    900: '#111827',
                }
            },
            keyframes: {
                'reveal-pop': {
                    '0%': { opacity: '0', transform: 'scale(0.8)' },
                    '100%': { opacity: '1', transform: 'scale(1)' },
                },
                'slide-up': {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'glow': {
                    '0%, 100%': { boxShadow: '0 0 10px rgba(255, 214, 36, 0.4)' },
                    '50%': { boxShadow: '0 0 30px rgba(255, 214, 36, 0.8)' },
                }
            },
            animation: {
                'reveal-pop': 'reveal-pop 0.7s ease-out',
                'slide-up': 'slide-up 0.6s ease-out',
                'fade-in': 'fade-in 0.8s ease-out',
                'glow': 'glow 2s ease-in-out infinite',
            },
            boxShadow: {
                'premium': '0 1px 3px rgba(0, 0, 0, 0.05), 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 20px 25px -5px rgba(0, 0, 0, 0.06)',
                'premium-lg': '0 4px 6px rgba(0, 0, 0, 0.05), 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 25px 50px -12px rgba(0, 0, 0, 0.08)',
            }
        },
    },
    plugins: [],
};
