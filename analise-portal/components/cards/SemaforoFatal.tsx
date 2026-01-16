'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Filtros } from '@/components/filtros/FiltrosAgenda'

interface SemaforoFatalProps {
  filtros: Filtros | null
  onCardClick: (categoria: string, diasMin?: number, diasMax?: number) => void
}

interface DadoCategoria {
  categoria: string
  quantidade: number
  cor: string
  ordem: number
}

export default function SemaforoFatal({ filtros, onCardClick }: SemaforoFatalProps) {
  const [dados, setDados] = useState<DadoCategoria[]>([])
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

      // Adicionar filtros (exceto prazo_fatal) - apenas se filtros existirem
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
      const response = await fetch(`/api/agenda/semaforo-fatal?${params.toString()}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      })
      if (response.ok) {
        const result = await response.json()
        setDados(result.dados)
        setTotal(result.total)
      }
    } catch (error) {
      console.error('Erro ao buscar dados do semáforo:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCardClick = (categoria: string) => {
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)

    let diasMin: number | undefined
    let diasMax: number | undefined

    // Calcular range de dias baseado na categoria
    switch (categoria) {
      case 'Possível perda':
        // Dias negativos, mas apenas a partir de 01/01/2026
        diasMin = undefined
        diasMax = -1
        break
      case 'Crítico':
        diasMin = 0
        diasMax = 0
        break
      case 'Atenção':
        diasMin = 1
        diasMax = 2
        break
      case 'Próximo':
        diasMin = 3
        diasMax = 5
        break
      case 'Normal':
        diasMin = 6
        diasMax = undefined
        break
    }

    onCardClick(categoria, diasMin, diasMax)
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {dados.map((item) => (
        <Card
          key={item.categoria}
          className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-105 border-2 hover:border-opacity-80"
          style={{ borderColor: item.cor }}
          onClick={() => handleCardClick(item.categoria)}
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800 text-sm">{item.categoria}</h3>
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: item.cor }}
              ></div>
            </div>
            <p className="text-3xl font-bold" style={{ color: item.cor }}>
              {item.quantidade.toLocaleString('pt-BR')}
            </p>
            {total > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {((item.quantidade / total) * 100).toFixed(1)}% do total
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
