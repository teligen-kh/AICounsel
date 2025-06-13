import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import MainLayout from '@/layouts/MainLayout';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '고객 지원 플랫폼',
  description: 'AI 기반 고객 지원 플랫폼',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
} 