import type { Metadata } from 'next';
import './globals.css';
import React from 'react';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'MF Assistant — Space Command Center',
  description: 'Facts-only Q&A for mutual fund schemes',
  metadataBase: new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full overflow-hidden font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
