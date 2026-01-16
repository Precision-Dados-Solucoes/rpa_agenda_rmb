'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import DetalhesUsuario from './DetalhesUsuario'
import { Eye } from 'lucide-react'

interface Usuario {
  id: string
  email: string
  nome: string
  role: string
  ativo: boolean
  senha_alterada: boolean
  paginas_autorizadas: string[]
  executantes_autorizados: string[]
  created_at: string
  updated_at: string
}

interface ListaUsuariosProps {
  refreshTrigger: number
}

export default function ListaUsuarios({ refreshTrigger }: ListaUsuariosProps) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [usuarioSelecionado, setUsuarioSelecionado] = useState<string | null>(null)

  useEffect(() => {
    buscarUsuarios()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger])

  const buscarUsuarios = async () => {
    setLoading(true)
    setErro(null)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setErro('Sessão expirada. Faça login novamente.')
        return
      }

      const response = await fetch('/api/usuarios', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()

      if (!response.ok) {
        setErro(data.error || 'Erro ao buscar usuários')
        return
      }

      setUsuarios(data.usuarios || [])
    } catch (error) {
      console.error('Erro ao buscar usuários:', error)
      setErro('Erro ao buscar usuários. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const formatarData = (data: string) => {
    return new Date(data).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getRoleBadge = (role: string) => {
    const roles: { [key: string]: { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } } = {
      administrador: { label: 'Administrador', variant: 'destructive' },
      gerente: { label: 'Gerente', variant: 'default' },
      usuario: { label: 'Usuário', variant: 'secondary' },
    }
    const roleInfo = roles[role] || { label: role, variant: 'outline' as const }
    return (
      <Badge variant={roleInfo.variant}>{roleInfo.label}</Badge>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Lista de Usuários</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-gray-500">Carregando usuários...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (erro) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Lista de Usuários</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{erro}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lista de Usuários</CardTitle>
        <p className="text-sm text-gray-600 mt-1">
          Total: {usuarios.length} usuário(s)
        </p>
      </CardHeader>
      <CardContent>
        {usuarios.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-gray-500">Nenhum usuário cadastrado</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold text-gray-700">Nome</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Email</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Perfil</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Status</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Senha Alterada</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Data de Criação</th>
                  <th className="text-left p-3 font-semibold text-gray-700">Ações</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((usuario) => (
                  <tr key={usuario.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{usuario.nome}</td>
                    <td className="p-3">{usuario.email}</td>
                    <td className="p-3">{getRoleBadge(usuario.role)}</td>
                    <td className="p-3">
                      {usuario.ativo ? (
                        <Badge variant="default" className="!bg-green-500 hover:!bg-green-600">Ativo</Badge>
                      ) : (
                        <Badge variant="secondary">Inativo</Badge>
                      )}
                    </td>
                    <td className="p-3">
                      {usuario.senha_alterada ? (
                        <Badge variant="default" className="!bg-blue-500 hover:!bg-blue-600">Sim</Badge>
                      ) : (
                        <Badge variant="secondary">Não</Badge>
                      )}
                    </td>
                    <td className="p-3 text-sm text-gray-600">
                      {formatarData(usuario.created_at)}
                    </td>
                    <td className="p-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setUsuarioSelecionado(usuario.id)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Ver Detalhes
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>

      {/* Modal de Detalhes */}
      {usuarioSelecionado && (
        <DetalhesUsuario
          usuarioId={usuarioSelecionado}
          onClose={() => {
            setUsuarioSelecionado(null)
            buscarUsuarios() // Atualizar lista após fechar
          }}
          onUsuarioAtualizado={() => {
            buscarUsuarios() // Atualizar lista após atualização
          }}
        />
      )}
    </Card>
  )
}
