'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft } from 'lucide-react'

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

interface DetalhesUsuarioProps {
  usuarioId: string
  onClose: () => void
  onUsuarioAtualizado: () => void
}

export default function DetalhesUsuario({
  usuarioId,
  onClose,
  onUsuarioAtualizado,
}: DetalhesUsuarioProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [carregandoExecutantes, setCarregandoExecutantes] = useState(true)
  const [executantes, setExecutantes] = useState<string[]>([])
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [formData, setFormData] = useState({
    nome: '',
    role: 'usuario',
    ativo: true,
    paginas: [] as string[],
    executantes: [] as string[],
    senha: '',
  })
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState(false)

  useEffect(() => {
    buscarUsuario()
    buscarExecutantes()
  }, [usuarioId])

  const buscarUsuario = async () => {
    setLoading(true)
    setErro(null)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setErro('Sessão expirada. Faça login novamente.')
        return
      }

      const response = await fetch(`/api/usuarios/${usuarioId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()

      if (!response.ok) {
        setErro(data.error || 'Erro ao buscar usuário')
        return
      }

      setUsuario(data.usuario)
      setFormData({
        nome: data.usuario.nome,
        role: data.usuario.role,
        ativo: data.usuario.ativo,
        paginas: data.usuario.paginas_autorizadas || [],
        executantes: data.usuario.executantes_autorizados || [],
        senha: '',
      })
    } catch (error) {
      console.error('Erro ao buscar usuário:', error)
      setErro('Erro ao buscar usuário. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const buscarExecutantes = async () => {
    try {
      const response = await fetch('/api/usuarios/executantes')
      if (response.ok) {
        const data = await response.json()
        setExecutantes(data.executantes || [])
      }
    } catch (error) {
      console.error('Erro ao buscar executantes:', error)
    } finally {
      setCarregandoExecutantes(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    setSucesso(false)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setErro('Sessão expirada. Faça login novamente.')
        return
      }

      const dadosEnvio: any = {
        nome: formData.nome,
        role: formData.role,
        ativo: formData.ativo,
      }

      // Incluir senha apenas se foi preenchida
      if (formData.senha && formData.senha.length >= 6) {
        dadosEnvio.senha = formData.senha
      }

      // Incluir permissões apenas se não for administrador
      if (formData.role !== 'administrador') {
        dadosEnvio.paginas = formData.paginas
        dadosEnvio.executantes = formData.executantes
      }

      const response = await fetch(`/api/usuarios/${usuarioId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(dadosEnvio),
      })

      const data = await response.json()

      if (!response.ok) {
        setErro(data.error || 'Erro ao atualizar usuário')
        return
      }

      setSucesso(true)
      setFormData({ ...formData, senha: '' }) // Limpar campo de senha
      onUsuarioAtualizado()

      // Limpar mensagem de sucesso após 3 segundos
      setTimeout(() => {
        setSucesso(false)
      }, 3000)
    } catch (error) {
      console.error('Erro ao atualizar usuário:', error)
      setErro('Erro ao atualizar usuário. Tente novamente.')
    } finally {
      setSalvando(false)
    }
  }

  if (loading) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Detalhes do Usuário</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-8">
            <p className="text-gray-500">Carregando...</p>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-6 w-6"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            Detalhes do Usuário
          </DialogTitle>
        </DialogHeader>

        {usuario && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={usuario.email} disabled />
              <p className="text-xs text-gray-500">O email não pode ser alterado</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="nome">Nome *</Label>
              <Input
                id="nome"
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                required
                placeholder="Nome completo"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role">Perfil *</Label>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData({ ...formData, role: value })}
              >
                <SelectTrigger id="role">
                  <SelectValue placeholder="Selecione o perfil" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="usuario">Usuário</SelectItem>
                  <SelectItem value="gerente">Gerente</SelectItem>
                  <SelectItem value="administrador">Administrador</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="ativo"
                  checked={formData.ativo}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, ativo: checked as boolean })
                  }
                />
                <Label htmlFor="ativo" className="font-normal cursor-pointer">
                  Usuário ativo
                </Label>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="senha">Nova Senha (deixe em branco para não alterar)</Label>
              <Input
                id="senha"
                type="password"
                value={formData.senha}
                onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
                placeholder="Mínimo 6 caracteres"
                minLength={6}
              />
            </div>

            {/* Páginas Autorizadas - apenas para não administradores */}
            {formData.role !== 'administrador' && (
              <>
                <div className="space-y-3">
                  <Label>Páginas Autorizadas *</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_pagina_agenda"
                        checked={formData.paginas.includes('dashboard_agenda')}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              paginas: [...formData.paginas, 'dashboard_agenda'],
                            })
                          } else {
                            setFormData({
                              ...formData,
                              paginas: formData.paginas.filter((p) => p !== 'dashboard_agenda'),
                            })
                          }
                        }}
                      />
                      <Label htmlFor="edit_pagina_agenda" className="font-normal cursor-pointer">
                        Dashboard de Agenda
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_pagina_indicadores"
                        checked={formData.paginas.includes('dashboard_indicadores')}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              paginas: [...formData.paginas, 'dashboard_indicadores'],
                            })
                          } else {
                            setFormData({
                              ...formData,
                              paginas: formData.paginas.filter((p) => p !== 'dashboard_indicadores'),
                            })
                          }
                        }}
                      />
                      <Label htmlFor="edit_pagina_indicadores" className="font-normal cursor-pointer">
                        Dashboard de Indicadores
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="edit_pagina_usuarios"
                        checked={formData.paginas.includes('gerenciamento_usuarios')}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              paginas: [...formData.paginas, 'gerenciamento_usuarios'],
                            })
                          } else {
                            setFormData({
                              ...formData,
                              paginas: formData.paginas.filter((p) => p !== 'gerenciamento_usuarios'),
                            })
                          }
                        }}
                      />
                      <Label htmlFor="edit_pagina_usuarios" className="font-normal cursor-pointer">
                        Gerenciamento de Usuários
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Executantes Autorizados - apenas para não administradores */}
                <div className="space-y-3">
                  <Label>Executantes Autorizados * (selecione ao menos 1)</Label>
                  {carregandoExecutantes ? (
                    <p className="text-sm text-gray-500">Carregando executantes...</p>
                  ) : (
                    <div className="border rounded-md p-4 max-h-60 overflow-y-auto space-y-2">
                      {executantes.length === 0 ? (
                        <p className="text-sm text-gray-500">Nenhum executante encontrado</p>
                      ) : (
                        executantes.map((executante) => (
                          <div key={executante} className="flex items-center space-x-2">
                            <Checkbox
                              id={`edit_exec_${executante}`}
                              checked={formData.executantes.includes(executante)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setFormData({
                                    ...formData,
                                    executantes: [...formData.executantes, executante],
                                  })
                                } else {
                                  setFormData({
                                    ...formData,
                                    executantes: formData.executantes.filter((e) => e !== executante),
                                  })
                                }
                              }}
                            />
                            <Label
                              htmlFor={`edit_exec_${executante}`}
                              className="font-normal cursor-pointer text-sm"
                            >
                              {executante}
                            </Label>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                  {formData.executantes.length > 0 && (
                    <p className="text-xs text-gray-500">
                      {formData.executantes.length} executante(s) selecionado(s)
                    </p>
                  )}
                </div>
              </>
            )}

            {formData.role === 'administrador' && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-600">
                  Administradores têm acesso total a todas as páginas e executantes.
                </p>
              </div>
            )}

            {erro && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{erro}</p>
              </div>
            )}

            {sucesso && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-sm text-green-600">Usuário atualizado com sucesso!</p>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  salvando ||
                  (formData.role !== 'administrador' &&
                    (formData.paginas.length === 0 || formData.executantes.length === 0))
                }
                className="flex-1"
              >
                {salvando ? 'Salvando...' : 'Salvar Alterações'}
              </Button>
            </div>
            {formData.role !== 'administrador' &&
              (formData.paginas.length === 0 || formData.executantes.length === 0) && (
                <p className="text-xs text-red-500 text-center">
                  {formData.paginas.length === 0 && 'Selecione ao menos uma página. '}
                  {formData.executantes.length === 0 && 'Selecione ao menos um executante.'}
                </p>
              )}
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
