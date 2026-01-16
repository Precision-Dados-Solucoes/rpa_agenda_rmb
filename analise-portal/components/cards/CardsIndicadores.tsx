'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface Indicadores {
  agendas: number
  produzidos: number
  antecipado: number
  noPrazo: number
  tardio: number
  cumprido: number
  comParecer: number
}

interface CardsIndicadoresProps {
  filtros: Filtros | null
}

export default function CardsIndicadores({ filtros }: CardsIndicadoresProps) {
  const [indicadores, setIndicadores] = useState<Indicadores>({
    agendas: 0,
    produzidos: 0,
    antecipado: 0,
    noPrazo: 0,
    tardio: 0,
    cumprido: 0,
    comParecer: 0,
  })
  const [carregando, setCarregando] = useState(false)

  useEffect(() => {
    buscarIndicadores()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  // Carregar indicadores iniciais quando componente montar
  useEffect(() => {
    if (!filtros) {
      buscarIndicadores()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const buscarIndicadores = async () => {
    setCarregando(true)
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

      const token = localStorage.getItem('token')
      const response = await fetch(`/api/indicadores?${params.toString()}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      })
      if (response.ok) {
        const data = await response.json()
        setIndicadores(data)
      } else {
        console.error('Erro ao buscar indicadores:', response.statusText)
      }
    } catch (error) {
      console.error('Erro ao buscar indicadores:', error)
    } finally {
      setCarregando(false)
    }
  }

  const cards = [
    {
      titulo: 'Agendas',
      valor: indicadores.agendas,
      cor: '#3b82f6', // blue
      icone: '📊',
    },
    {
      titulo: 'Produzidos',
      valor: indicadores.produzidos,
      cor: '#8b5cf6', // purple
      icone: '✅',
    },
    {
      titulo: 'Antecipado',
      valor: indicadores.antecipado,
      cor: '#10b981', // green
      icone: '⏰',
    },
    {
      titulo: 'No prazo',
      valor: indicadores.noPrazo,
      cor: '#3b82f6', // blue
      icone: '⏱️',
    },
    {
      titulo: 'Tardio',
      valor: indicadores.tardio,
      cor: '#ef4444', // red
      icone: '⚠️',
    },
    {
      titulo: 'Cumprido',
      valor: indicadores.cumprido,
      cor: '#10b981', // green
      icone: '✓',
    },
    {
      titulo: 'Com parecer',
      valor: indicadores.comParecer,
      cor: '#f59e0b', // amber
      icone: '📝',
    },
  ]

  if (carregando) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
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
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4">
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
