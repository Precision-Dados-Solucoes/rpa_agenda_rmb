'use client'

// Esta página será a mesma que estava em /dashboard
// Vamos mover o conteúdo atual para cá
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Drawer } from '@/components/ui/drawer'
import { Filter } from 'lucide-react'
import FiltrosAgenda, { Filtros } from '@/components/filtros/FiltrosAgenda'
import GraficoExecutante from '@/components/graficos/GraficoExecutante'
import GraficoComplexidade from '@/components/graficos/GraficoComplexidade'
import GraficoStatus from '@/components/graficos/GraficoStatus'
import GraficoTipo from '@/components/graficos/GraficoTipo'
import GraficoSubtipo from '@/components/graficos/GraficoSubtipo'
import SemaforoFatal from '@/components/cards/SemaforoFatal'
import MetricasAgenda from '@/components/cards/MetricasAgenda'
import GridAgenda from '@/components/agenda/GridAgenda'
import ModalDetalhes from '@/components/agenda/ModalDetalhes'

export default function DashboardAgendaPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filtros, setFiltros] = useState<Filtros | null>(null)
  const [dados, setDados] = useState<any[]>([])
  const [carregandoDados, setCarregandoDados] = useState(false)
  const [paginacao, setPaginacao] = useState({
    total: 0,
    page: 1,
    limit: 100,
    totalPages: 0,
  })
  const [itemDetalhes, setItemDetalhes] = useState<any>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [filtrosExternos, setFiltrosExternos] = useState<Partial<Filtros>>({})
  const [erroConexao, setErroConexao] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (!token || !userStr) {
      router.push('/login')
      return
    }

    setUser(JSON.parse(userStr))
    setLoading(false)
  }, [router])

  const buscarDados = useCallback(async (filtrosAtuais: Filtros, pagina: number = 1) => {
    setCarregandoDados(true)
    setErroConexao(null) // Limpar erro anterior
    try {
      const params = new URLSearchParams()

      if (filtrosAtuais.executante && filtrosAtuais.executante !== 'Todos') {
        params.append('executante', filtrosAtuais.executante)
      }
      if (filtrosAtuais.status && filtrosAtuais.status !== 'Todos') {
        params.append('status', filtrosAtuais.status)
      }
      if (filtrosAtuais.complexidade && filtrosAtuais.complexidade !== 'Todos') {
        params.append('complexidade', filtrosAtuais.complexidade)
      }
      if (filtrosAtuais.tipo && filtrosAtuais.tipo !== 'Todos') {
        params.append('tipo', filtrosAtuais.tipo)
      }
      if (filtrosAtuais.pasta && filtrosAtuais.pasta !== 'Todos') {
        params.append('pasta', filtrosAtuais.pasta)
      }

      if (filtrosAtuais.dataInicioFrom) {
        params.append('dataInicioFrom', filtrosAtuais.dataInicioFrom)
      }
      if (filtrosAtuais.dataInicioTo) {
        params.append('dataInicioTo', filtrosAtuais.dataInicioTo)
      }
      if (filtrosAtuais.conclusaoPrevistaFrom) {
        params.append('conclusaoPrevistaFrom', filtrosAtuais.conclusaoPrevistaFrom)
      }
      if (filtrosAtuais.conclusaoPrevistaTo) {
        params.append('conclusaoPrevistaTo', filtrosAtuais.conclusaoPrevistaTo)
      }
      if (filtrosAtuais.conclusaoEfetivaFrom) {
        params.append('conclusaoEfetivaFrom', filtrosAtuais.conclusaoEfetivaFrom)
      }
      if (filtrosAtuais.conclusaoEfetivaTo) {
        params.append('conclusaoEfetivaTo', filtrosAtuais.conclusaoEfetivaTo)
      }
      if (filtrosAtuais.prazoFatalFrom) {
        params.append('prazoFatalFrom', filtrosAtuais.prazoFatalFrom)
      }
      if (filtrosAtuais.prazoFatalTo) {
        params.append('prazoFatalTo', filtrosAtuais.prazoFatalTo)
      }

      params.append('page', pagina.toString())
      params.append('limit', paginacao.limit.toString())

      const response = await fetch(`/api/agenda/dados?${params.toString()}`)
      if (response.ok) {
        const result = await response.json()
        setDados(result.dados)
        setPaginacao(result.paginacao)
      } else {
        // Tentar ler o JSON de erro, mas tratar caso não seja válido
        let errorData: any = null
        try {
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            errorData = await response.json()
          } else {
            const text = await response.text()
            errorData = { message: text || 'Erro desconhecido' }
          }
        } catch (parseError) {
          errorData = { 
            message: `Erro ${response.status}: ${response.statusText}`,
            details: 'Não foi possível ler a resposta do servidor'
          }
        }
        console.error('Erro na resposta:', response.status, response.statusText, errorData)
        
        // Definir mensagem de erro amigável
        if (response.status === 503 || errorData?.error?.toLowerCase().includes('conexão') || errorData?.error?.toLowerCase().includes('banco')) {
          setErroConexao(errorData?.details || 'O servidor de banco de dados pode estar hibernando ou indisponível. Aguarde alguns instantes e tente novamente.')
        } else {
          setErroConexao(errorData?.error || errorData?.message || 'Erro ao buscar dados. Tente novamente.')
        }
        
        setDados([])
        setPaginacao((prev) => ({ ...prev, total: 0, page: 1, totalPages: 0 }))
      }
    } catch (error) {
      console.error('Erro ao buscar dados:', error)
      setErroConexao('Erro ao conectar com o servidor. Verifique sua conexão e tente novamente.')
      setDados([])
      setPaginacao((prev) => ({ ...prev, total: 0, page: 1, totalPages: 0 }))
    } finally {
      setCarregandoDados(false)
    }
  }, [paginacao.limit])

  useEffect(() => {
    if (!filtros) {
      const filtrosVazios: Filtros = {
        executante: 'Todos',
        status: 'Todos',
        complexidade: 'Todos',
        tipo: 'Todos',
        pasta: 'Todos',
        dataInicioFrom: '',
        dataInicioTo: '',
        conclusaoPrevistaFrom: '',
        conclusaoPrevistaTo: '',
        conclusaoEfetivaFrom: '',
        conclusaoEfetivaTo: '',
        prazoFatalFrom: '',
        prazoFatalTo: '',
      }
      setFiltros(filtrosVazios)
    } else {
      buscarDados(filtros, paginacao.page)
    }
  }, [filtros, buscarDados, paginacao.page])

  const handleFiltrosChange = useCallback((novosFiltros: Filtros) => {
    setFiltros(novosFiltros)
    setPaginacao((prev) => ({ ...prev, page: 1 }))
  }, [])

  const handleCardClick = useCallback((categoria: string, diasMin?: number, diasMax?: number) => {
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)

    let dataFrom: string | undefined
    let dataTo: string | undefined

    if (categoria === 'Possível perda') {
      dataFrom = '2026-01-01'
    } else {
      if (diasMin !== undefined) {
        const dataMin = new Date(hoje)
        dataMin.setDate(dataMin.getDate() + diasMin)
        dataFrom = dataMin.toISOString().split('T')[0]
      }

      if (diasMax !== undefined) {
        const dataMax = new Date(hoje)
        dataMax.setDate(dataMax.getDate() + diasMax)
        dataTo = dataMax.toISOString().split('T')[0]
      }
    }

    setFiltrosExternos({
      prazoFatalFrom: dataFrom,
      prazoFatalTo: dataTo,
    })
  }, [])

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
            <Button
              onClick={() => setDrawerOpen(true)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filtros
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Dashboard de Agenda</h1>
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
            <Button 
              onClick={() => router.push('/dashboard/indicadores')} 
              variant="outline"
              size="sm"
            >
              Dashboard de Indicadores
            </Button>
          </div>
        </div>

        {/* Drawer com Filtros */}
        <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} title="Filtros" side="left">
          <FiltrosAgenda 
            onFiltrosChange={handleFiltrosChange} 
            filtrosExternos={filtrosExternos}
            compact={true}
          />
        </Drawer>

        {/* Mensagem de Erro de Conexão */}
        {erroConexao && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-red-800 mb-1">Erro de Conexão</h3>
                <p className="text-sm text-red-600">{erroConexao}</p>
              </div>
              <button
                onClick={() => setErroConexao(null)}
                className="text-red-400 hover:text-red-600 ml-4"
                aria-label="Fechar mensagem"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Cards de Métricas */}
        <MetricasAgenda filtros={filtros} />

        {/* Cards Semáforo do Fatal */}
        <div>
          <h2 className="text-xl font-bold mb-4">Semáforo do Fatal</h2>
          <SemaforoFatal filtros={filtros} onCardClick={handleCardClick} />
        </div>

        {/* Layout: Gráficos à esquerda, Grid à direita */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Coluna Esquerda: Gráficos */}
          <div className="lg:col-span-2 space-y-6">
            {/* Gráfico por Executante */}
            <GraficoExecutante filtros={filtros} />

            {/* Gráficos Adicionais */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GraficoComplexidade filtros={filtros} />
              <GraficoStatus filtros={filtros} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GraficoTipo filtros={filtros} />
              <GraficoSubtipo filtros={filtros} />
            </div>
          </div>

          {/* Coluna Direita: Grid de Cards */}
          <div className="lg:col-span-1">
            <Card className="h-[1348px] flex flex-col">
              <CardHeader>
                <CardTitle>Resultados</CardTitle>
                <CardDescription>
                  {paginacao.total > 0 ? (
                    <>Total de {paginacao.total.toLocaleString('pt-BR')} registro(s)</>
                  ) : (
                    'Nenhum registro encontrado'
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col min-h-0">
                <GridAgenda
                  dados={dados}
                  carregando={carregandoDados}
                  onItemClick={setItemDetalhes}
                  paginacao={paginacao}
                  onPageChange={(page) => setPaginacao((prev) => ({ ...prev, page }))}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <ModalDetalhes item={itemDetalhes} onClose={() => setItemDetalhes(null)} />
    </div>
  )
}
