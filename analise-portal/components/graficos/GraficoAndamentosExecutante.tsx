'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, Cell } from 'recharts'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface GraficoAndamentosExecutanteProps {
  filtros: Filtros | null
}

interface DadoGrafico {
  executante: string
  quantidade: number
}

interface DetalheAndamento {
  tipo: string
  quantidade: number
}

// Função para extrair abreviação do nome
const extrairAbreviacao = (nome: string): string => {
  const palavras = nome.trim().split(/\s+/)
  if (palavras.length === 0) return ''

  const iniciais = palavras
    .slice(0, 4)
    .map((palavra) => palavra.charAt(0).toUpperCase())
    .join('')

  return iniciais
}

// Função para formatar nome com abreviação
const formatarNome = (nome: string): string => {
  const abreviacao = extrairAbreviacao(nome)
  return `${nome} (${abreviacao})`
}

export default function GraficoAndamentosExecutante({ filtros }: GraficoAndamentosExecutanteProps) {
  const [dados, setDados] = useState<DadoGrafico[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [detalhesAbertos, setDetalhesAbertos] = useState(false)
  const [executanteSelecionado, setExecutanteSelecionado] = useState<string | null>(null)
  const [detalhes, setDetalhes] = useState<DetalheAndamento[]>([])
  const [carregandoDetalhes, setCarregandoDetalhes] = useState(false)

  useEffect(() => {
    buscarDados()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  // Carregar dados iniciais quando componente montar
  useEffect(() => {
    if (!filtros) {
      buscarDados()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const buscarDados = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      if (filtros?.executante && filtros.executante !== 'Todos') {
        params.append('executante', filtros.executante)
      }
      if (filtros?.status && filtros.status !== 'Todos') {
        params.append('status', filtros.status)
      }
      if (filtros?.complexidade && filtros.complexidade !== 'Todos') {
        params.append('complexidade', filtros.complexidade)
      }
      if (filtros?.tipo && filtros.tipo !== 'Todos') {
        params.append('tipo', filtros.tipo)
      }
      if (filtros?.pasta && filtros.pasta !== 'Todos') {
        params.append('pasta', filtros.pasta)
      }

      if (filtros?.dataInicioFrom) {
        params.append('dataInicioFrom', filtros.dataInicioFrom)
      }
      if (filtros?.dataInicioTo) {
        params.append('dataInicioTo', filtros.dataInicioTo)
      }
      if (filtros?.conclusaoPrevistaFrom) {
        params.append('conclusaoPrevistaFrom', filtros.conclusaoPrevistaFrom)
      }
      if (filtros?.conclusaoPrevistaTo) {
        params.append('conclusaoPrevistaTo', filtros.conclusaoPrevistaTo)
      }
      if (filtros?.conclusaoEfetivaFrom) {
        params.append('conclusaoEfetivaFrom', filtros.conclusaoEfetivaFrom)
      }
      if (filtros?.conclusaoEfetivaTo) {
        params.append('conclusaoEfetivaTo', filtros.conclusaoEfetivaTo)
      }
      if (filtros?.prazoFatalFrom) {
        params.append('prazoFatalFrom', filtros.prazoFatalFrom)
      }
      if (filtros?.prazoFatalTo) {
        params.append('prazoFatalTo', filtros.prazoFatalTo)
      }

      const response = await fetch(`/api/indicadores/andamentos-executante?${params.toString()}`)
      if (response.ok) {
        const result = await response.json()
        setDados(result.dados)
        setTotal(result.total)
      }
    } catch (error) {
      console.error('Erro ao buscar dados do gráfico:', error)
    } finally {
      setLoading(false)
    }
  }

  const abrirDetalhes = async (executante: string) => {
    setExecutanteSelecionado(executante)
    setDetalhesAbertos(true)
    setCarregandoDetalhes(true)

    try {
      const params = new URLSearchParams()
      // O executante selecionado é o parâmetro principal
      params.append('executante', executante)

      // Adicionar todos os outros filtros aplicados (exceto executante que já foi adicionado)
      if (filtros?.status && filtros.status !== 'Todos') {
        params.append('status', filtros.status)
      }
      if (filtros?.status && filtros.status !== 'Todos') {
        params.append('status', filtros.status)
      }
      if (filtros?.complexidade && filtros.complexidade !== 'Todos') {
        params.append('complexidade', filtros.complexidade)
      }
      if (filtros?.tipo && filtros.tipo !== 'Todos') {
        params.append('tipo', filtros.tipo)
      }
      if (filtros?.pasta && filtros.pasta !== 'Todos') {
        params.append('pasta', filtros.pasta)
      }

      if (filtros?.dataInicioFrom) {
        params.append('dataInicioFrom', filtros.dataInicioFrom)
      }
      if (filtros?.dataInicioTo) {
        params.append('dataInicioTo', filtros.dataInicioTo)
      }
      if (filtros?.conclusaoPrevistaFrom) {
        params.append('conclusaoPrevistaFrom', filtros.conclusaoPrevistaFrom)
      }
      if (filtros?.conclusaoPrevistaTo) {
        params.append('conclusaoPrevistaTo', filtros.conclusaoPrevistaTo)
      }
      if (filtros?.conclusaoEfetivaFrom) {
        params.append('conclusaoEfetivaFrom', filtros.conclusaoEfetivaFrom)
      }
      if (filtros?.conclusaoEfetivaTo) {
        params.append('conclusaoEfetivaTo', filtros.conclusaoEfetivaTo)
      }
      if (filtros?.prazoFatalFrom) {
        params.append('prazoFatalFrom', filtros.prazoFatalFrom)
      }
      if (filtros?.prazoFatalTo) {
        params.append('prazoFatalTo', filtros.prazoFatalTo)
      }

      const response = await fetch(`/api/indicadores/andamentos-detalhes?${params.toString()}`)
      if (response.ok) {
        const result = await response.json()
        setDetalhes(result.dados)
      }
    } catch (error) {
      console.error('Erro ao buscar detalhes:', error)
    } finally {
      setCarregandoDetalhes(false)
    }
  }

  // Preparar dados para o gráfico com nome formatado
  const dadosFormatados = dados.map((item) => ({
    ...item,
    executanteFormatado: formatarNome(item.executante),
  }))

  // Cor para as barras
  const COR_BARRA = '#3b82f6' // azul

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Visão de Andamentos por Executante</CardTitle>
          {total > 0 && (
            <p className="text-sm text-gray-600 mt-2">
              Total: {total.toLocaleString('pt-BR')} registro(s)
            </p>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <p className="text-gray-500">Carregando gráfico...</p>
            </div>
          ) : dados.length === 0 ? (
            <div className="flex items-center justify-center h-96">
              <p className="text-gray-500">Nenhum dado disponível</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(500, dados.length * 60)}>
              <BarChart
                data={dadosFormatados}
                layout="vertical"
                margin={{ top: 20, right: 80, left: 150, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="executanteFormatado"
                  width={140}
                  tick={{ fontSize: 12 }}
                  interval={0}
                />
                <Tooltip
                  formatter={(value) => [typeof value === 'number' ? value.toLocaleString('pt-BR') : String(value || 0), 'Quantidade']}
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
                <Bar
                  dataKey="quantidade"
                  fill={COR_BARRA}
                  radius={[0, 4, 4, 0]}
                >
                  {dadosFormatados.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      onClick={() => abrirDetalhes(entry.executante)}
                      style={{ cursor: 'pointer' }}
                    />
                  ))}
                  <LabelList
                    dataKey="quantidade"
                    position="right"
                    offset={10}
                    formatter={(value) => typeof value === 'number' ? value.toLocaleString('pt-BR') : String(value || 0)}
                    style={{ fill: '#374151', fontSize: '12px', fontWeight: 600 }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Modal de Detalhes */}
      <Dialog open={detalhesAbertos} onOpenChange={setDetalhesAbertos}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Detalhes de Andamentos - {executanteSelecionado}
            </DialogTitle>
            <DialogDescription>
              Quantidade de andamentos por tipo
            </DialogDescription>
          </DialogHeader>
          {carregandoDetalhes ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-gray-500">Carregando detalhes...</p>
            </div>
          ) : detalhes.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-gray-500">Nenhum detalhe disponível</p>
            </div>
          ) : (
            <div className="mt-4 space-y-2">
              {detalhes.map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-sm font-medium text-gray-700">{item.tipo}</span>
                  <span className="text-sm font-bold text-blue-600">
                    {item.quantidade.toLocaleString('pt-BR')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
