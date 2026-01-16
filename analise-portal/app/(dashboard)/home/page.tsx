'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, BarChart3, Users, LogOut } from 'lucide-react'
import { temAcessoPagina, PermissoesUsuario } from '@/lib/permissoes-helper'

export default function HomePage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [permissoes, setPermissoes] = useState<PermissoesUsuario | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (!token || !userStr) {
      router.push('/login')
      return
    }

    const userData = JSON.parse(userStr)
    setUser(userData)
    
    // Construir objeto de permissões
    const permissoesData: PermissoesUsuario = {
      paginas_autorizadas: userData.paginas_autorizadas || [],
      executantes_autorizados: userData.executantes_autorizados || [],
      role: userData.role || 'usuario',
    }
    setPermissoes(permissoesData)
    setLoading(false)
  }, [router])

  const handleLogout = async () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Carregando...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-800 mb-3">
            Advocacia Roberto Matos de Brito
          </h1>
          <h2 className="text-2xl font-semibold text-blue-600 uppercase tracking-wide">
            Portal de Análises
          </h2>
          <div className="mt-6 flex items-center justify-center gap-4">
            <p className="text-gray-600">
              Bem-vindo, <span className="font-semibold text-slate-800">{user?.nome}</span>
            </p>
            <span className="text-gray-400">•</span>
            <p className="text-gray-600">
              <span className="font-semibold text-slate-800">{user?.role}</span>
            </p>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="ml-4"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sair
            </Button>
          </div>
        </div>

        {/* Cards de Navegação */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {/* Dashboard de Agenda */}
          <Card className="hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-blue-500 group h-full flex flex-col">
            <CardContent className="p-8 flex flex-col flex-1">
              <div
                onClick={() => router.push('/dashboard/agenda')}
                className="flex flex-col items-center text-center h-full"
              >
                <div className="bg-blue-100 p-6 rounded-full group-hover:bg-blue-200 transition-colors">
                  <Calendar className="h-12 w-12 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mt-4">Dashboard de Agenda</h3>
                <p className="text-gray-600 text-sm mt-2 flex-1">
                  Visualize e analise os dados da agenda com gráficos e métricas detalhadas
                </p>
                <Button className="w-full mt-4" variant="default">
                  Acessar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Dashboard de Indicadores */}
          <Card className="hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-green-500 group h-full flex flex-col">
            <CardContent className="p-8 flex flex-col flex-1">
              <div
                onClick={() => router.push('/dashboard/indicadores')}
                className="flex flex-col items-center text-center h-full"
              >
                <div className="bg-green-100 p-6 rounded-full group-hover:bg-green-200 transition-colors">
                  <BarChart3 className="h-12 w-12 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mt-4">Dashboard de Indicadores</h3>
                <p className="text-gray-600 text-sm mt-2 flex-1">
                  Acompanhe indicadores de performance e métricas estratégicas do negócio
                </p>
                <Button className="w-full mt-4" variant="default">
                  Acessar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Usuários - Apenas se tiver permissão */}
          {temAcessoPagina(permissoes, 'gerenciamento_usuarios') && (
            <Card className="hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-purple-500 group h-full flex flex-col">
              <CardContent className="p-8 flex flex-col flex-1">
                <div
                  onClick={() => router.push('/dashboard/usuarios')}
                  className="flex flex-col items-center text-center h-full"
                >
                  <div className="bg-purple-100 p-6 rounded-full group-hover:bg-purple-200 transition-colors">
                    <Users className="h-12 w-12 text-purple-600" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-800 mt-4">Usuários</h3>
                  <p className="text-gray-600 text-sm mt-2 flex-1">
                    Gerencie usuários, permissões e acessos do sistema
                  </p>
                  <Button className="w-full mt-4" variant="default">
                    Acessar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Debug - Disponível para todos os usuários logados para diagnóstico */}
          {user && (
            <Card className="hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-orange-500 group h-full flex flex-col">
              <CardContent className="p-8 flex flex-col flex-1">
                <div
                  onClick={() => router.push('/dashboard/debug-permissoes')}
                  className="flex flex-col items-center text-center h-full"
                >
                  <div className="bg-orange-100 p-6 rounded-full group-hover:bg-orange-200 transition-colors">
                    <span className="text-4xl">🔍</span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-800 mt-4">Debug Permissões</h3>
                  <p className="text-gray-600 text-sm mt-2 flex-1">
                    Diagnóstico de permissões e controle de acesso
                    {user.role !== 'administrador' && (
                      <span className="block mt-1 text-xs text-orange-600">
                        (Verifique suas limitações)
                      </span>
                    )}
                  </p>
                  <Button className="w-full mt-4" variant="default">
                    Acessar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
