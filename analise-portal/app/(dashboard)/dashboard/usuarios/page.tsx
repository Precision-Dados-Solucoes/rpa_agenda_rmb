'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import FormularioUsuario from '@/components/usuarios/FormularioUsuario'
import ListaUsuarios from '@/components/usuarios/ListaUsuarios'

export default function UsuariosPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (!token || !userStr) {
      router.push('/login')
      return
    }

    const userData = JSON.parse(userStr)
    setUser(userData)
    
    // Verificar se é administrador ou gerente
    if (userData.role !== 'administrador' && userData.role !== 'gerente') {
      router.push('/home')
      return
    }

    setLoading(false)
  }, [router])

  const handleLogout = async () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const handleUsuarioCriado = () => {
    // Atualizar lista de usuários
    setRefreshTrigger((prev) => prev + 1)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Carregando...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              onClick={() => router.push('/home')}
              variant="outline"
              size="sm"
            >
              ← Voltar
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Gerenciamento de Usuários</h1>
              <p className="text-gray-600">
                Bem-vindo, {user?.nome} ({user?.role})
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Button 
              onClick={handleLogout} 
              variant="outline"
              className="bg-red-500 hover:bg-red-600 text-white border-red-500 hover:border-red-600"
            >
              Sair
            </Button>
          </div>
        </div>

        {/* Formulário de Cadastro (apenas para administradores) */}
        {user?.role === 'administrador' && (
          <FormularioUsuario onUsuarioCriado={handleUsuarioCriado} />
        )}

        {/* Lista de Usuários */}
        <ListaUsuarios refreshTrigger={refreshTrigger} />
      </div>
    </div>
  )
}
