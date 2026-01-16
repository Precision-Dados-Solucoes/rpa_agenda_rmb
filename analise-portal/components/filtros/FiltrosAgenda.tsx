'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface FiltrosAgendaProps {
  onFiltrosChange: (filtros: Filtros) => void
  filtrosExternos?: Partial<Filtros>
  compact?: boolean // Se true, remove o Card wrapper
}

export interface Filtros {
  executante: string
  status: string
  complexidade: string
  tipo: string
  pasta: string
  dataInicioFrom: string
  dataInicioTo: string
  conclusaoPrevistaFrom: string
  conclusaoPrevistaTo: string
  conclusaoEfetivaFrom: string
  conclusaoEfetivaTo: string
  prazoFatalFrom: string
  prazoFatalTo: string
}

interface OpcoesFiltros {
  executantes: string[]
  status: string[]
  complexidades: string[]
  tipos: string[]
  pastas: string[]
  ranges: {
    dataInicio: { min: string | null; max: string | null }
    conclusaoPrevista: { min: string | null; max: string | null }
    conclusaoEfetiva: { min: string | null; max: string | null }
    prazoFatal: { min: string | null; max: string | null }
  }
}

export default function FiltrosAgenda({ onFiltrosChange, filtrosExternos, compact = false }: FiltrosAgendaProps) {
  const [opcoes, setOpcoes] = useState<OpcoesFiltros>({
    executantes: [],
    status: [],
    complexidades: [],
    tipos: [],
    pastas: [],
    ranges: {
      dataInicio: { min: null, max: null },
      conclusaoPrevista: { min: null, max: null },
      conclusaoEfetiva: { min: null, max: null },
      prazoFatal: { min: null, max: null },
    },
  })

  const [filtros, setFiltros] = useState<Filtros>({
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
  })

  const [loading, setLoading] = useState(true)

  // Carregar opções dos filtros
  useEffect(() => {
    async function carregarOpcoes() {
      try {
        const response = await fetch('/api/agenda/filtros')
        if (response.ok) {
          const data = await response.json()
          setOpcoes(data)
        }
      } catch (error) {
        console.error('Erro ao carregar opções de filtros:', error)
      } finally {
        setLoading(false)
      }
    }
    carregarOpcoes()
  }, [])

  // Atualizar filtros quando houver mudança externa
  useEffect(() => {
    if (filtrosExternos) {
      setFiltros((prev) => ({ ...prev, ...filtrosExternos }))
    }
  }, [filtrosExternos])

  // Notificar mudanças nos filtros
  useEffect(() => {
    onFiltrosChange(filtros)
  }, [filtros, onFiltrosChange])

  const handleChange = (campo: keyof Filtros, valor: string) => {
    setFiltros((prev) => ({ ...prev, [campo]: valor }))
  }

  const limparFiltros = () => {
    setFiltros({
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
    })
  }

  if (loading) {
    return (
      <div className="p-6">
        <p className="text-center text-gray-500">Carregando filtros...</p>
      </div>
    )
  }

  const content = (
    <div className="space-y-8">
      {/* Dropdowns */}
      <div className="space-y-6">
        <h3 className="text-base font-semibold text-gray-800 border-b pb-2">Filtros Principais</h3>
        <div className="grid grid-cols-1 gap-5">
          <div className="space-y-2">
            <Label htmlFor="executante" className="text-sm font-medium text-gray-700">Executante</Label>
            <select
              id="executante"
              value={filtros.executante}
              onChange={(e) => handleChange('executante', e.target.value)}
              className="w-full h-11 px-4 rounded-md border border-gray-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Todos">Todos</option>
              {opcoes.executantes.map((exec) => (
                <option key={exec} value={exec}>
                  {exec}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="status" className="text-sm font-medium text-gray-700">Status</Label>
            <select
              id="status"
              value={filtros.status}
              onChange={(e) => handleChange('status', e.target.value)}
              className="w-full h-11 px-4 rounded-md border border-gray-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Todos">Todos</option>
              {opcoes.status.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="complexidade" className="text-sm font-medium text-gray-700">Complexidade</Label>
            <select
              id="complexidade"
              value={filtros.complexidade}
              onChange={(e) => handleChange('complexidade', e.target.value)}
              className="w-full h-11 px-4 rounded-md border border-gray-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Todos">Todos</option>
              {opcoes.complexidades.map((comp) => (
                <option key={comp} value={comp}>
                  {comp}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tipo" className="text-sm font-medium text-gray-700">Tipo</Label>
            <select
              id="tipo"
              value={filtros.tipo}
              onChange={(e) => handleChange('tipo', e.target.value)}
              className="w-full h-11 px-4 rounded-md border border-gray-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Todos">Todos</option>
              {opcoes.tipos.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="pasta" className="text-sm font-medium text-gray-700">Pasta</Label>
            <select
              id="pasta"
              value={filtros.pasta}
              onChange={(e) => handleChange('pasta', e.target.value)}
              className="w-full h-11 px-4 rounded-md border border-gray-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Todos">Todos</option>
              {opcoes.pastas.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Separador visual */}
      <div className="border-t border-gray-200 my-6"></div>

      {/* Date Ranges */}
      <div className="space-y-6">
        <h3 className="text-base font-semibold text-gray-800 border-b pb-2">Filtros de Data</h3>
        <div className="grid grid-cols-1 gap-6">
          {/* Data de Início */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-800 mb-5 text-base">Data de Início</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dataInicioFrom" className="text-sm text-gray-700 font-medium">De</Label>
                <Input
                  id="dataInicioFrom"
                  type="date"
                  value={filtros.dataInicioFrom}
                  onChange={(e) => handleChange('dataInicioFrom', e.target.value)}
                  className="w-full h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dataInicioTo" className="text-sm text-gray-700 font-medium">Até</Label>
                <Input
                  id="dataInicioTo"
                  type="date"
                  value={filtros.dataInicioTo}
                  onChange={(e) => handleChange('dataInicioTo', e.target.value)}
                  className="w-full h-11"
                />
              </div>
            </div>
          </div>

          {/* Conclusão Prevista */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-800 mb-5 text-base">Conclusão Prevista</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="conclusaoPrevistaFrom" className="text-sm text-gray-700 font-medium">De</Label>
                <Input
                  id="conclusaoPrevistaFrom"
                  type="date"
                  value={filtros.conclusaoPrevistaFrom}
                  onChange={(e) => handleChange('conclusaoPrevistaFrom', e.target.value)}
                  className="w-full h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="conclusaoPrevistaTo" className="text-sm text-gray-700 font-medium">Até</Label>
                <Input
                  id="conclusaoPrevistaTo"
                  type="date"
                  value={filtros.conclusaoPrevistaTo}
                  onChange={(e) => handleChange('conclusaoPrevistaTo', e.target.value)}
                  className="w-full h-11"
                />
              </div>
            </div>
          </div>

          {/* Conclusão Efetiva */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-800 mb-5 text-base">Conclusão Efetiva</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="conclusaoEfetivaFrom" className="text-sm text-gray-700 font-medium">De</Label>
                <Input
                  id="conclusaoEfetivaFrom"
                  type="date"
                  value={filtros.conclusaoEfetivaFrom}
                  onChange={(e) => handleChange('conclusaoEfetivaFrom', e.target.value)}
                  className="w-full h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="conclusaoEfetivaTo" className="text-sm text-gray-700 font-medium">Até</Label>
                <Input
                  id="conclusaoEfetivaTo"
                  type="date"
                  value={filtros.conclusaoEfetivaTo}
                  onChange={(e) => handleChange('conclusaoEfetivaTo', e.target.value)}
                  className="w-full h-11"
                />
              </div>
            </div>
          </div>

          {/* Prazo Fatal */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-800 mb-5 text-base">Prazo Fatal</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="prazoFatalFrom" className="text-sm text-gray-700 font-medium">De</Label>
                <Input
                  id="prazoFatalFrom"
                  type="date"
                  value={filtros.prazoFatalFrom}
                  onChange={(e) => handleChange('prazoFatalFrom', e.target.value)}
                  className="w-full h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prazoFatalTo" className="text-sm text-gray-700 font-medium">Até</Label>
                <Input
                  id="prazoFatalTo"
                  type="date"
                  value={filtros.prazoFatalTo}
                  onChange={(e) => handleChange('prazoFatalTo', e.target.value)}
                  className="w-full h-11"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  if (compact) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center pb-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Filtros</h2>
          <Button variant="outline" size="sm" onClick={limparFiltros}>
            Limpar Filtros
          </Button>
        </div>
        {content}
      </div>
    )
  }

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Filtros</CardTitle>
          <Button variant="outline" size="sm" onClick={limparFiltros}>
            Limpar Filtros
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {content}
      </CardContent>
    </Card>
  )
}
