import type { Metadata } from 'next'
import { Providers } from './providers'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { ChatWidget } from '@/components/shared/ChatWidget'
import './globals.css'

export const metadata: Metadata = {
  title: 'CyberScore',
  description: 'Plateforme souveraine de cyber scoring et VRM',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr">
      <body className="bg-[#F7F9FA] text-[#2C3E50]">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="ml-64 flex flex-1 flex-col">
              <Header />
              <main className="flex-1 p-6">{children}</main>
            </div>
          </div>
          <ChatWidget />
        </Providers>
      </body>
    </html>
  )
}
