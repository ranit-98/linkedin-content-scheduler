import type { Metadata } from 'next';
import { Manrope } from 'next/font/google';
import type { ReactNode } from 'react';
import Providers from './providers';
import './styles.css';

const manrope = Manrope({ subsets: ['latin'], variable: '--font-manrope' });
export const metadata: Metadata = {
  title: 'PostPilot — LinkedIn Scheduler',
  description: 'Schedule LinkedIn posts with confidence.',
};
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={manrope.variable}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
