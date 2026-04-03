/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,

	// Enable SWC minification for better performance
	swcMinify: true,

	// Environment variables available to the browser
	env: {
		NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
	},

	// Optimize images if needed in the future
	images: {
		remotePatterns: [],
	},

	// Webpack configuration for path aliases (already handled by Next.js)
	webpack: (config) => {
		return config;
	},
};

module.exports = nextConfig;
