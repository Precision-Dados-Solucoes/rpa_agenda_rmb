'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink, FileText, Calendar, User, Tag } from 'lucide-react'
import ModalDetalhes from './ModalDetalhes'

interface ItemAgenda {
  id_legalone: bigint | number
  compromisso_tarefa: string | null
  tipo: string | null
  subtipo: string | null
  etiqueta: string | null
  inicio_data: Date | string | null
  conclusao_prevista_data: Date | string | null
  conclusao_efetiva_data: Date | string | null
  prazo_fatal_data: Date | string | null
  pasta_proc: string | null
  numero_cnj: string | null
  executante: string | null
  descricao: string | null
  status: string | null
  link: string | null
  quantidadeAndamentos: number
}

interface GridAgendaProps {
  dados: ItemAgenda[]
  carregando: boolean
  onPageChange: (page: number) => void
  paginacao: {
    total: number
    page: number
    limit: number
    totalPages: number
  }
}

export default function GridAgenda({ dados, carregando, onPageChange, paginacao }: GridAgendaProps) {
  const [itemSelecionado, setItemSelecionado] = useState<ItemAgenda | null>(null)

  const formatarData = (data: Date | string | null) => {
    if (!data) return '-'
    const date = typeof data === 'string' ? new Date(data) : data
    return date.toLocaleDateString('pt-BR')
  }

  const formatarStatus = (status: string | null) => {
    if (!status) return '-'
    const statusLower = status.toLowerCase()
    if (statusLower.includes('cumprido')) {
      return 'Cumprido'
    }
    if (statusLower.includes('pendente')) {
      return 'Pendente'
    }
    return status
  }

  const getStatusColor = (status: string | null) => {
    if (!status) return 'bg-gray-100 text-gray-800'
    const statusLower = status.toLowerCase()
    if (statusLower.includes('cumprido')) {
      return 'bg-green-100 text-green-800'
    }
    if (statusLower.includes('pendente')) {
      return 'bg-yellow-100 text-yellow-800'
    }
    return 'bg-gray-100 text-gray-800'
  }

  if (carregando) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-center text-gray-500">Carregando dados...</p>
        </CardContent>
      </Card>
    )
  }

  if (dados.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-center text-gray-500">Nenhum registro encontrado</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <div className="space-y-3 flex-1 overflow-y-auto pr-2">
        {dados.map((item) => (
          <Card
            key={item.id_legalone.toString()}
            className="cursor-pointer hover:shadow-md transition-shadow border-l-4 border-l-blue-500"
            onClick={() => setItemSelecionado(item)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-gray-900">
                      ID: {item.id_legalone.toString()}
                    </span>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.status)}`}
                    >
                      {formatarStatus(item.status)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium">{item.compromisso_tarefa || 'N/A'}</span>
                  </div>

                  {item.executante && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <User className="h-4 w-4" />
                      <span>{item.executante}</span>
                    </div>
                  )}

                  {item.subtipo && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Tag className="h-4 w-4" />
                      <span>{item.subtipo}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                    {item.prazo_fatal_data && (
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>Fatal: {formatarData(item.prazo_fatal_data)}</span>
                      </div>
                    )}
                    {item.quantidadeAndamentos > 0 && (
                      <div className="flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        <span>{item.quantidadeAndamentos} andamento(s)</span>
                      </div>
                    )}
                  </div>
                </div>

                {item.link && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex-shrink-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      window.open(item.link!, '_blank')
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Paginação */}
      {paginacao.totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-4 pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            disabled={paginacao.page === 1}
            onClick={() => onPageChange(paginacao.page - 1)}
          >
            Anterior
          </Button>
          <span className="text-sm text-gray-600 px-4">
            Página {paginacao.page} de {paginacao.totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={paginacao.page === paginacao.totalPages}
            onClick={() => onPageChange(paginacao.page + 1)}
          >
            Próxima
          </Button>
        </div>
      )}

      {/* Modal de Detalhes */}
      {itemSelecionado && (
        <ModalDetalhes
          item={itemSelecionado}
          onClose={() => setItemSelecionado(null)}
        />
      )}
    </>
  )
}
