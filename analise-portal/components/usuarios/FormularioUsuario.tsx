'use client'

import { useState, useEffect } from 'react'
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

interface FormularioUsuarioProps {
  onUsuarioCriado: () => void
}

export default function FormularioUsuario({ onUsuarioCriado }: FormularioUsuarioProps) {
  const [loading, setLoading] = useState(false)
  const [carregandoExecutantes, setCarregandoExecutantes] = useState(true)
  const [executantes, setExecutantes] = useState<string[]>([])
  const [formData, setFormData] = useState({
    email: '',
    senha: '',
    nome: '',
    role: 'usuario',
    paginas: [] as string[],
    executantes: [] as string[],
  })
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState(false)

  useEffect(() => {
    buscarExecutantes()
  }, [])

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
    setLoading(true)
    setErro(null)
    setSucesso(false)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setErro('Sessão expirada. Faça login novamente.')
        return
      }

      const response = await fetch('/api/usuarios', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (!response.ok) {
        setErro(data.error || 'Erro ao criar usuário')
        return
      }

      setSucesso(true)
      setFormData({
        email: '',
        senha: '',
        nome: '',
        role: 'usuario',
        paginas: [],
        executantes: [],
      })
      
      // Notificar componente pai
      onUsuarioCriado()
      
      // Limpar mensagem de sucesso após 3 segundos
      setTimeout(() => {
        setSucesso(false)
      }, 3000)
    } catch (error) {
      console.error('Erro ao criar usuário:', error)
      setErro('Erro ao criar usuário. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cadastrar Novo Usuário</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              placeholder="email@exemplo.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="senha">Senha *</Label>
            <Input
              id="senha"
              type="password"
              value={formData.senha}
              onChange={(e) => setFormData({ ...formData, senha: e.target.value })}
              required
              placeholder="Senha do usuário"
              minLength={6}
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

          {/* Páginas Autorizadas - apenas para não administradores */}
          {formData.role !== 'administrador' && (
            <>
              <div className="space-y-3">
                <Label>Páginas Autorizadas *</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pagina_agenda"
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
                    <Label htmlFor="pagina_agenda" className="font-normal cursor-pointer">
                      Dashboard de Agenda
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pagina_indicadores"
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
                    <Label htmlFor="pagina_indicadores" className="font-normal cursor-pointer">
                      Dashboard de Indicadores
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pagina_usuarios"
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
                    <Label htmlFor="pagina_usuarios" className="font-normal cursor-pointer">
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
                            id={`exec_${executante}`}
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
                            htmlFor={`exec_${executante}`}
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
              <p className="text-sm text-green-600">Usuário criado com sucesso!</p>
            </div>
          )}

          <Button
            type="submit"
            disabled={
              loading ||
              (formData.role !== 'administrador' &&
                (formData.paginas.length === 0 || formData.executantes.length === 0))
            }
            className="w-full"
          >
            {loading ? 'Criando...' : 'Criar Usuário'}
          </Button>
          {formData.role !== 'administrador' &&
            (formData.paginas.length === 0 || formData.executantes.length === 0) && (
              <p className="text-xs text-red-500 text-center">
                {formData.paginas.length === 0 && 'Selecione ao menos uma página. '}
                {formData.executantes.length === 0 && 'Selecione ao menos um executante.'}
              </p>
            )}
        </form>
      </CardContent>
    </Card>
  )
}
