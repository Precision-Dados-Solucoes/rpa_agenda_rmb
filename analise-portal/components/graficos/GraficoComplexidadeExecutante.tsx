'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LabelList } from 'recharts'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface GraficoComplexidadeExecutanteProps {
  filtros: Filtros | null
}

interface DadoGrafico {
  executante: string
  alta: number
  media: number
  baixa: number
  total: number
  altaPercent: number
  mediaPercent: number
  baixaPercent: number
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

export default function GraficoComplexidadeExecutante({ filtros }: GraficoComplexidadeExecutanteProps) {
  const [dados, setDados] = useState<DadoGrafico[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

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

      const response = await fetch(`/api/indicadores/complexidade-executante?${params.toString()}`)
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

  // Preparar dados para o gráfico com nome formatado
  const dadosFormatados = dados.map((item) => ({
    ...item,
    executanteFormatado: formatarNome(item.executante),
  }))

  // Cores para as barras
  const COR_ALTA = '#ef4444' // vermelho
  const COR_BAIXA = '#10b981' // verde
  const COR_MEDIA = '#f59e0b' // amarelo

  return (
    <Card>
      <CardHeader>
        <CardTitle>Visão de Complexidade por Executante da Produção</CardTitle>
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
                formatter={(value, name) => {
                  const labels: { [key: string]: string } = {
                    alta: 'Alta Complexidade',
                    media: 'Média Complexidade',
                    baixa: 'Baixa Complexidade',
                  }
                  const label = labels[String(name)] || String(name)
                  const numValue = typeof value === 'number' ? value : 0
                  return [`${numValue.toFixed(1)}%`, label]
                }}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                iconType="circle"
                formatter={(value: string) => {
                  const labels: { [key: string]: string } = {
                    alta: 'Alta Complexidade',
                    media: 'Média Complexidade',
                    baixa: 'Baixa Complexidade',
                  }
                  return labels[value] || value
                }}
              />
              <Bar
                dataKey="altaPercent"
                stackId="a"
                fill={COR_ALTA}
                name="alta"
              >
                <LabelList
                  dataKey="altaPercent"
                  position="inside"
                  formatter={(value: number) => (value > 0 ? `${value.toFixed(0)}%` : '')}
                  style={{ fill: '#fff', fontSize: '11px', fontWeight: 500 }}
                />
              </Bar>
              <Bar
                dataKey="baixaPercent"
                stackId="a"
                fill={COR_BAIXA}
                name="baixa"
              >
                <LabelList
                  dataKey="baixaPercent"
                  position="inside"
                  formatter={(value: number) => (value > 0 ? `${value.toFixed(0)}%` : '')}
                  style={{ fill: '#fff', fontSize: '11px', fontWeight: 500 }}
                />
              </Bar>
              <Bar
                dataKey="mediaPercent"
                stackId="a"
                fill={COR_MEDIA}
                name="media"
              >
                <LabelList
                  dataKey="mediaPercent"
                  position="inside"
                  formatter={(value: number) => (value > 0 ? `${value.toFixed(0)}%` : '')}
                  style={{ fill: '#fff', fontSize: '11px', fontWeight: 500 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
