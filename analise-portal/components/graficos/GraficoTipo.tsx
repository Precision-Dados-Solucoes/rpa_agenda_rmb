'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface GraficoTipoProps {
  filtros: Filtros | null
}

interface DadoGrafico {
  tipo: string
  quantidade: number
}

export default function GraficoTipo({ filtros }: GraficoTipoProps) {
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

      const response = await fetch(`/api/agenda/grafico-tipo?${params.toString()}`)
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

  const formatarNome = (nome: string) => {
    if (nome.length > 15) {
      return nome.substring(0, 12) + '...'
    }
    return nome
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Tipo</CardTitle>
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
          <CardTitle>Tipo</CardTitle>
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
        <CardTitle>Tipo</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={dados}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="tipo"
              angle={-45}
              textAnchor="end"
              height={80}
              tick={{ fontSize: 12 }}
              interval={0}
              tickFormatter={formatarNome}
            />
            <YAxis hide />
            <Tooltip
              formatter={(value) => [typeof value === 'number' ? value.toLocaleString('pt-BR'), 'Quantidade']}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
              }}
            />
            <Bar dataKey="quantidade" radius={[4, 4, 0, 0]} fill="#3b82f6">
              <LabelList
                dataKey="quantidade"
                position="top"
                formatter={(value) => typeof value === 'number' ? value.toLocaleString('pt-BR')}
                style={{ fontSize: '12px', fill: '#374151', fontWeight: 500 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
