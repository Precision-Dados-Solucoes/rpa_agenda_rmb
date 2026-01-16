import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Portal de Análise de Dados',
  description: 'Sistema de análise de dados multi-tenant',
  metadataBase: new URL(process.env.NEXTAUTH_URL || 'https://advromas.precisionsolucoes.com'),
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
