import "./globals.css";

export const metadata = {
  title: "ZKONER — AI Brand Visibility Diagnostic",
  description: "Check how AI understands your brand. Get your AI Visibility Score and growth roadmap.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
