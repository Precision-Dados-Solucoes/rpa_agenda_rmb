'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Drawer } from '@/components/ui/drawer'
import { Filter } from 'lucide-react'
import FiltrosAgenda, { Filtros } from '@/components/filtros/FiltrosAgenda'
import CardsIndicadores from '@/components/cards/CardsIndicadores'
import GraficoProducaoExecutante from '@/components/graficos/GraficoProducaoExecutante'
import GraficoComplexidadeExecutante from '@/components/graficos/GraficoComplexidadeExecutante'
import GraficoAndamentosExecutante from '@/components/graficos/GraficoAndamentosExecutante'
import GraficoReagendamentosExecutante from '@/components/graficos/GraficoReagendamentosExecutante'
import GraficoRetornosExecutante from '@/components/graficos/GraficoRetornosExecutante'

export default function DashboardIndicadoresPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filtros, setFiltros] = useState<Filtros | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [filtrosExternos, setFiltrosExternos] = useState<Partial<Filtros>>({})

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
    }
  }, [filtros])

  const handleFiltrosChange = useCallback((novosFiltros: Filtros) => {
    setFiltros(novosFiltros)
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
              <h1 className="text-3xl font-bold">Dashboard de Indicadores</h1>
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
              onClick={() => router.push('/dashboard/agenda')} 
              variant="outline"
              size="sm"
            >
              Dashboard de Agenda
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

        {/* Cards de Indicadores */}
        <CardsIndicadores filtros={filtros} />

        {/* Gráfico de Produção por Executante */}
        <GraficoProducaoExecutante filtros={filtros} />

        {/* Gráfico de Complexidade por Executante */}
        <GraficoComplexidadeExecutante filtros={filtros} />

        {/* Gráfico de Andamentos por Executante */}
        <GraficoAndamentosExecutante filtros={filtros} />

        {/* Gráfico de Reagendamentos por Executante */}
        <GraficoReagendamentosExecutante filtros={filtros} />

        {/* Gráfico de Retornos por Executante */}
        <GraficoRetornosExecutante filtros={filtros} />
      </div>
    </div>
  )
}
