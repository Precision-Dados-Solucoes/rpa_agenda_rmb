'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function DebugPermissoesPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [dados, setDados] = useState<any>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    verificarPermissoes()
  }, [router])

  const verificarPermissoes = async () => {
    setLoading(true)
    setErro(null)

    try {
      const token = localStorage.getItem('token')
      const userStr = localStorage.getItem('user')

      // Dados do localStorage
      const userLocalStorage = userStr ? JSON.parse(userStr) : null

      // Testar endpoint de debug
      const response = await fetch('/api/debug/permissoes', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      const data = await response.json()

      setDados({
        localStorage: {
          user: userLocalStorage,
          token: token ? token.substring(0, 20) + '...' : null,
        },
        api: data,
      })
    } catch (error) {
      setErro(error instanceof Error ? error.message : String(error))
    } finally {
      setLoading(false)
    }
  }

  const testarAPI = async (endpoint: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      const data = await response.json()
      alert(`Status: ${response.status}\n\nResposta:\n${JSON.stringify(data, null, 2)}`)
    } catch (error) {
      alert(`Erro: ${error instanceof Error ? error.message : String(error)}`)
    }
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
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">🔍 Diagnóstico de Permissões</h1>
          <Button onClick={() => router.push('/home')} variant="outline">
            ← Voltar
          </Button>
        </div>

        {erro && (
          <Card className="border-red-500">
            <CardHeader>
              <CardTitle className="text-red-600">❌ Erro</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="whitespace-pre-wrap text-sm">{erro}</pre>
            </CardContent>
          </Card>
        )}

        {dados && (
          <>
            {/* Dados do localStorage */}
            <Card>
              <CardHeader>
                <CardTitle>📦 Dados no localStorage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <strong>Token:</strong> {dados.localStorage.token || '❌ Não encontrado'}
                  </div>
                  <div>
                    <strong>Usuário:</strong>
                    <pre className="mt-2 p-3 bg-gray-100 rounded text-sm overflow-auto">
                      {JSON.stringify(dados.localStorage.user, null, 2)}
                    </pre>
                  </div>
                  {dados.localStorage.user && (
                    <div className="space-y-2">
                      <div>
                        <strong>Páginas Autorizadas:</strong>
                        <div className="mt-1">
                          {dados.localStorage.user.paginas_autorizadas?.length > 0 ? (
                            <ul className="list-disc list-inside">
                              {dados.localStorage.user.paginas_autorizadas.map((p: string) => (
                                <li key={p}>{p}</li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-yellow-600">⚠️ Array vazio ou não definido</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <strong>Executantes Autorizados:</strong>
                        <div className="mt-1">
                          {dados.localStorage.user.executantes_autorizados?.length > 0 ? (
                            <ul className="list-disc list-inside">
                              {dados.localStorage.user.executantes_autorizados.map((e: string) => (
                                <li key={e}>{e}</li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-yellow-600">
                              ⚠️ Array vazio = acesso a TODOS os executantes
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Dados da API */}
            <Card>
              <CardHeader>
                <CardTitle>🔌 Dados da API (/api/debug/permissoes)</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="whitespace-pre-wrap text-sm overflow-auto bg-gray-100 p-3 rounded">
                  {JSON.stringify(dados.api, null, 2)}
                </pre>
              </CardContent>
            </Card>

            {/* Testes de APIs */}
            <Card>
              <CardHeader>
                <CardTitle>🧪 Testar APIs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button
                    onClick={() => testarAPI('/api/agenda/dados?page=1&limit=5')}
                    variant="outline"
                    className="w-full"
                  >
                    Testar /api/agenda/dados
                  </Button>
                  <Button
                    onClick={() => testarAPI('/api/agenda/grafico-executante')}
                    variant="outline"
                    className="w-full"
                  >
                    Testar /api/agenda/grafico-executante
                  </Button>
                  <Button
                    onClick={() => testarAPI('/api/indicadores/producao-executante')}
                    variant="outline"
                    className="w-full"
                  >
                    Testar /api/indicadores/producao-executante
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Button onClick={verificarPermissoes} className="w-full">
              🔄 Atualizar Diagnóstico
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
