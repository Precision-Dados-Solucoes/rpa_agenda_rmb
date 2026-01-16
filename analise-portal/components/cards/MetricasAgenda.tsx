'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface MetricasAgendaProps {
  filtros: Filtros | null
}

interface Metricas {
  compromissos: number
  tarefas: number
  hoje: number
  atrasados: number
  emConferencia: number
  fatal: number
}

export default function MetricasAgenda({ filtros }: MetricasAgendaProps) {
  const [metricas, setMetricas] = useState<Metricas>({
    compromissos: 0,
    tarefas: 0,
    hoje: 0,
    atrasados: 0,
    emConferencia: 0,
    fatal: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    buscarMetricas()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  // Carregar métricas iniciais quando componente montar
  useEffect(() => {
    if (!filtros) {
      buscarMetricas()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const buscarMetricas = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      // Adicionar filtros (exceto prazo_fatal)
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

      // Adicionar filtros de data (exceto prazo_fatal)
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

      const token = localStorage.getItem('token')
      const response = await fetch(`/api/agenda/metricas?${params.toString()}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      })
      if (response.ok) {
        const result = await response.json()
        setMetricas(result)
      }
    } catch (error) {
      console.error('Erro ao buscar métricas:', error)
    } finally {
      setLoading(false)
    }
  }

  const cards = [
    {
      titulo: 'Compromissos',
      valor: metricas.compromissos,
      cor: '#3b82f6', // blue
      icone: '📅',
    },
    {
      titulo: 'Tarefas',
      valor: metricas.tarefas,
      cor: '#8b5cf6', // purple
      icone: '✓',
    },
    {
      titulo: 'Hoje',
      valor: metricas.hoje,
      cor: '#f59e0b', // amber
      icone: '📌',
    },
    {
      titulo: 'Atrasados',
      valor: metricas.atrasados,
      cor: '#ef4444', // red
      icone: '⚠️',
    },
    {
      titulo: 'Em Conferência',
      valor: metricas.emConferencia,
      cor: '#10b981', // green
      icone: '👁️',
    },
    {
      titulo: 'Fatal',
      valor: metricas.fatal,
      cor: '#f97316', // orange
      icone: '🔴',
    },
  ]

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <Card
          key={card.titulo}
          className="hover:shadow-lg transition-all duration-200 border-l-4"
          style={{ borderLeftColor: card.cor }}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">{card.icone}</span>
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: card.cor }}
              ></div>
            </div>
            <h3 className="text-sm font-semibold text-gray-700 mb-1">
              {card.titulo}
            </h3>
            <p className="text-2xl font-bold" style={{ color: card.cor }}>
              {card.valor.toLocaleString('pt-BR')}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
