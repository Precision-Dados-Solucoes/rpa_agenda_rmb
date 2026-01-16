'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface GraficoExecutanteProps {
  filtros: Filtros | null
}

interface DadoGrafico {
  executante: string
  quantidade: number
}

export default function GraficoExecutante({ filtros }: GraficoExecutanteProps) {
  const [dados, setDados] = useState<DadoGrafico[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [filtrosAplicados, setFiltrosAplicados] = useState<string[]>([])

  useEffect(() => {
    buscarDados()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  const buscarDados = async () => {
    if (!filtros) return

    setLoading(true)
    try {
      const params = new URLSearchParams()

      // Adicionar filtros de dropdown
      if (filtros.executante && filtros.executante !== 'Todos') {
        params.append('executante', filtros.executante)
      }
      if (filtros.status && filtros.status !== 'Todos') {
        params.append('status', filtros.status)
      }
      if (filtros.complexidade && filtros.complexidade !== 'Todos') {
        params.append('complexidade', filtros.complexidade)
      }
      if (filtros.tipo && filtros.tipo !== 'Todos') {
        params.append('tipo', filtros.tipo)
      }
      if (filtros.pasta && filtros.pasta !== 'Todos') {
        params.append('pasta', filtros.pasta)
      }

      // Adicionar filtros de data
      if (filtros.dataInicioFrom) {
        params.append('dataInicioFrom', filtros.dataInicioFrom)
      }
      if (filtros.dataInicioTo) {
        params.append('dataInicioTo', filtros.dataInicioTo)
      }
      if (filtros.conclusaoPrevistaFrom) {
        params.append('conclusaoPrevistaFrom', filtros.conclusaoPrevistaFrom)
      }
      if (filtros.conclusaoPrevistaTo) {
        params.append('conclusaoPrevistaTo', filtros.conclusaoPrevistaTo)
      }
      if (filtros.conclusaoEfetivaFrom) {
        params.append('conclusaoEfetivaFrom', filtros.conclusaoEfetivaFrom)
      }
      if (filtros.conclusaoEfetivaTo) {
        params.append('conclusaoEfetivaTo', filtros.conclusaoEfetivaTo)
      }
      if (filtros.prazoFatalFrom) {
        params.append('prazoFatalFrom', filtros.prazoFatalFrom)
      }
      if (filtros.prazoFatalTo) {
        params.append('prazoFatalTo', filtros.prazoFatalTo)
      }

      const response = await fetch(`/api/agenda/grafico-executante?${params.toString()}`)
      if (response.ok) {
        const result = await response.json()
        setDados(result.dados)
        setTotal(result.total)
        
        // Construir lista de filtros aplicados para exibição
        const filtrosTexto: string[] = []
        if (filtros.executante && filtros.executante !== 'Todos') {
          filtrosTexto.push(`Executante = '${filtros.executante}'`)
        }
        if (filtros.status && filtros.status !== 'Todos') {
          filtrosTexto.push(`Status = '${filtros.status}'`)
        }
        if (filtros.complexidade && filtros.complexidade !== 'Todos') {
          filtrosTexto.push(`Complexidade = '${filtros.complexidade}'`)
        }
        if (filtros.tipo && filtros.tipo !== 'Todos') {
          filtrosTexto.push(`Tipo = '${filtros.tipo}'`)
        }
        if (filtros.pasta && filtros.pasta !== 'Todos') {
          filtrosTexto.push(`Pasta = '${filtros.pasta}'`)
        }
        if (filtros.dataInicioFrom || filtros.dataInicioTo) {
          const de = filtros.dataInicioFrom ? new Date(filtros.dataInicioFrom).toLocaleDateString('pt-BR') : ''
          const ate = filtros.dataInicioTo ? new Date(filtros.dataInicioTo).toLocaleDateString('pt-BR') : ''
          filtrosTexto.push(`Data Início: ${de} ${ate ? 'até ' + ate : ''}`)
        }
        if (filtros.conclusaoPrevistaFrom || filtros.conclusaoPrevistaTo) {
          const de = filtros.conclusaoPrevistaFrom ? new Date(filtros.conclusaoPrevistaFrom).toLocaleDateString('pt-BR') : ''
          const ate = filtros.conclusaoPrevistaTo ? new Date(filtros.conclusaoPrevistaTo).toLocaleDateString('pt-BR') : ''
          filtrosTexto.push(`Conclusão Prevista: ${de} ${ate ? 'até ' + ate : ''}`)
        }
        if (filtros.conclusaoEfetivaFrom || filtros.conclusaoEfetivaTo) {
          const de = filtros.conclusaoEfetivaFrom ? new Date(filtros.conclusaoEfetivaFrom).toLocaleDateString('pt-BR') : ''
          const ate = filtros.conclusaoEfetivaTo ? new Date(filtros.conclusaoEfetivaTo).toLocaleDateString('pt-BR') : ''
          filtrosTexto.push(`Conclusão Efetiva: ${de} ${ate ? 'até ' + ate : ''}`)
        }
        if (filtros.prazoFatalFrom || filtros.prazoFatalTo) {
          const de = filtros.prazoFatalFrom ? new Date(filtros.prazoFatalFrom).toLocaleDateString('pt-BR') : ''
          const ate = filtros.prazoFatalTo ? new Date(filtros.prazoFatalTo).toLocaleDateString('pt-BR') : ''
          filtrosTexto.push(`Prazo Fatal: ${de} ${ate ? 'até ' + ate : ''}`)
        }
        setFiltrosAplicados(filtrosTexto)
      }
    } catch (error) {
      console.error('Erro ao buscar dados do gráfico:', error)
    } finally {
      setLoading(false)
    }
  }

  // Cores para as barras (gradiente de azul)
  const cores = [
    '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
    '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
    '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
  ]

  // Formatar nome do executante para exibição (truncar se muito longo)
  const formatarNome = (nome: string) => {
    if (nome.length > 20) {
      return nome.substring(0, 17) + '...'
    }
    return nome
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <CardTitle>Visão por Executante</CardTitle>
          {filtrosAplicados.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {filtrosAplicados.map((filtro, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {filtro}
                </span>
              ))}
            </div>
          )}
        </div>
        {total > 0 && (
          <p className="text-sm text-gray-600 mt-2">
            Total: {total.toLocaleString('pt-BR')} registro(s)
          </p>
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Carregando gráfico...</p>
          </div>
        ) : dados.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Nenhum dado disponível</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={dados}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="executante"
                angle={-45}
                textAnchor="end"
                height={100}
                tick={{ fontSize: 12 }}
                interval={0}
                tickFormatter={formatarNome}
              />
              <YAxis hide />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString('pt-BR'), 'Quantidade']}
                labelFormatter={(label: string) => `Executante: ${label}`}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                }}
              />
              <Bar dataKey="quantidade" radius={[4, 4, 0, 0]}>
                {dados.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={cores[index % cores.length]} />
                ))}
                <LabelList
                  dataKey="quantidade"
                  position="top"
                  formatter={(value: number) => value.toLocaleString('pt-BR')}
                  style={{ fontSize: '12px', fill: '#374151', fontWeight: 500 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
