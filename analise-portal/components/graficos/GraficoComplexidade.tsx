'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface GraficoComplexidadeProps {
  filtros: Filtros | null
}

interface DadoGrafico {
  complexidade: string
  quantidade: number
  [key: string]: string | number
}

export default function GraficoComplexidade({ filtros }: GraficoComplexidadeProps) {
  const [dados, setDados] = useState<DadoGrafico[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    buscarDados()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

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
      if (filtros?.executante && filtros.executante !== 'Todos') params.append('executante', filtros.executante)
      if (filtros?.status && filtros.status !== 'Todos') params.append('status', filtros.status)
      if (filtros?.complexidade && filtros.complexidade !== 'Todos') params.append('complexidade', filtros.complexidade)
      if (filtros?.tipo && filtros.tipo !== 'Todos') params.append('tipo', filtros.tipo)
      if (filtros?.pasta && filtros.pasta !== 'Todos') params.append('pasta', filtros.pasta)
      if (filtros?.dataInicioFrom) params.append('dataInicioFrom', filtros.dataInicioFrom)
      if (filtros?.dataInicioTo) params.append('dataInicioTo', filtros.dataInicioTo)
      if (filtros?.conclusaoPrevistaFrom) params.append('conclusaoPrevistaFrom', filtros.conclusaoPrevistaFrom)
      if (filtros?.conclusaoPrevistaTo) params.append('conclusaoPrevistaTo', filtros.conclusaoPrevistaTo)
      if (filtros?.conclusaoEfetivaFrom) params.append('conclusaoEfetivaFrom', filtros.conclusaoEfetivaFrom)
      if (filtros?.conclusaoEfetivaTo) params.append('conclusaoEfetivaTo', filtros.conclusaoEfetivaTo)
      if (filtros?.prazoFatalFrom) params.append('prazoFatalFrom', filtros.prazoFatalFrom)
      if (filtros?.prazoFatalTo) params.append('prazoFatalTo', filtros.prazoFatalTo)

      const response = await fetch(`/api/agenda/grafico-complexidade?${params.toString()}`)
      if (response.ok) {
        const result = await response.json()
        setDados(result.dados)
      }
    } catch (error) {
      console.error('Erro ao buscar dados:', error)
    } finally {
      setLoading(false)
    }
  }

  // Cores específicas para as 3 categorias de complexidade
  const getCorComplexidade = (complexidade: string) => {
    if (complexidade === 'Alta Complexidade') return '#ef4444' // red
    if (complexidade === 'Média Complexidade') return '#f59e0b' // amber
    if (complexidade === 'Baixa Complexidade') return '#22c55e' // green
    return '#6b7280' // gray (fallback)
  }

  const renderCustomLabel = (props: any) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, quantidade } = props
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        fontSize={12}
        fontWeight={500}
      >
        {quantidade.toLocaleString('pt-BR')}
      </text>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Complexidade</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Carregando...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (dados.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Complexidade</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Nenhum dado disponível</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Complexidade</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={dados}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              outerRadius={100}
              innerRadius={60}
              fill="#8884d8"
              dataKey="quantidade"
              nameKey="complexidade"
            >
              {dados.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getCorComplexidade(entry.complexidade)} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string, props: any) => [
                value.toLocaleString('pt-BR'),
                props.payload.complexidade
              ]}
              labelFormatter={() => ''}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
              }}
            />
            <Legend
              formatter={(value, entry: any) => {
                // entry.payload contém os dados completos do item
                if (entry && entry.payload) {
                  const complexidade = entry.payload.complexidade || value
                  const quantidade = entry.payload.quantidade || 0
                  return `${complexidade} (${quantidade.toLocaleString('pt-BR')})`
                }
                // Fallback: buscar nos dados
                const item = dados.find((d) => d.complexidade === value)
                if (item) {
                  return `${item.complexidade} (${item.quantidade.toLocaleString('pt-BR')})`
                }
                return value
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
