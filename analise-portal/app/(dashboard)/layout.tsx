'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const token = localStorage.getItem('token')

    if (!token) {
      router.push('/login')
      return
    }

    // Verificar se token é válido (pode adicionar verificação mais robusta)
    // Por enquanto, apenas verifica se existe
  }, [router])

  return <>{children}</>
}
