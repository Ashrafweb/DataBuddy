import { Inter, Manrope, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
	subsets: ["latin"],
	variable: "--font-inter",
	display: "swap",
});

const manrope = Manrope({
	subsets: ["latin"],
	variable: "--font-manrope",
	display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
	subsets: ["latin"],
	variable: "--font-jetbrains",
	display: "swap",
});

export const metadata = {
	title: "Smart SQL - Database Query Assistant",
	description: "Ask questions about your database in natural language",
};

export default function RootLayout({ children }) {
	return (
		<html lang='en' className='dark'>
			<body
				className={`${inter.variable} ${manrope.variable} ${jetbrainsMono.variable}`}
			>
				{children}
			</body>
		</html>
	);
}
