'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ExternalLink, Calendar, User, Tag, FileText, Building2 } from 'lucide-react'

interface ItemAgenda {
  id_legalone: bigint | number
  compromisso_tarefa: string | null
  tipo: string | null
  subtipo: string | null
  etiqueta: string | null
  inicio_data: Date | string | null
  inicio_hora: Date | string | null
  conclusao_prevista_data: Date | string | null
  conclusao_prevista_hora: Date | string | null
  conclusao_efetiva_data: Date | string | null
  prazo_fatal_data: Date | string | null
  pasta_proc: string | null
  numero_cnj: string | null
  executante: string | null
  executante_sim: string | null
  descricao: string | null
  status: string | null
  link: string | null
  cadastro: Date | string | null
  cliente_processo: string | null
  quantidadeAndamentos: number
}

interface ModalDetalhesProps {
  item: ItemAgenda | null
  onClose: () => void
}

export default function ModalDetalhes({ item, onClose }: ModalDetalhesProps) {
  const formatarData = (data: Date | string | null) => {
    if (!data) return '-'
    const date = typeof data === 'string' ? new Date(data) : data
    return date.toLocaleDateString('pt-BR')
  }

  const formatarHora = (hora: Date | string | null) => {
    if (!hora) return '-'
    const date = typeof hora === 'string' ? new Date(hora) : hora
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  if (!item) {
    return null
  }

  return (
    <Dialog open={!!item} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle>
                Detalhes do Item - ID: {typeof item.id_legalone === 'bigint' ? item.id_legalone.toString() : item.id_legalone}
              </DialogTitle>
              <DialogDescription className="mt-1">
                Informações completas do compromisso/tarefa
              </DialogDescription>
            </div>
            {item.link && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(item.link!, '_blank')}
                className="flex-shrink-0"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Abrir no Legal One
              </Button>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Informações Básicas */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Compromisso/Tarefa</label>
              <p className="text-sm font-semibold">{item.compromisso_tarefa || '-'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <p className="text-sm font-semibold">{item.status || '-'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Tipo</label>
              <p className="text-sm">{item.tipo || '-'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Subtipo</label>
              <p className="text-sm">{item.subtipo || '-'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Complexidade</label>
              <p className="text-sm">{item.etiqueta || '-'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Andamentos</label>
              <p className="text-sm font-semibold">{item.quantidadeAndamentos || 0}</p>
            </div>
          </div>

          {/* Executante */}
          {item.executante && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <User className="h-4 w-4" />
                Executante
              </label>
              <p className="text-sm mt-1">{item.executante}</p>
              {item.executante_sim && (
                <p className="text-xs text-gray-500 mt-1">Confirmado: {item.executante_sim}</p>
              )}
            </div>
          )}

          {/* Datas */}
          <div className="border-t pt-4">
            <label className="text-sm font-medium text-gray-500 flex items-center gap-2 mb-3">
              <Calendar className="h-4 w-4" />
              Datas e Prazos
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500">Data de Início</label>
                <p className="text-sm">
                  {formatarData(item.inicio_data)}
                  {item.inicio_hora && ` às ${formatarHora(item.inicio_hora)}`}
                </p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Conclusão Prevista</label>
                <p className="text-sm">
                  {formatarData(item.conclusao_prevista_data)}
                  {item.conclusao_prevista_hora && ` às ${formatarHora(item.conclusao_prevista_hora)}`}
                </p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Conclusão Efetiva</label>
                <p className="text-sm">{formatarData(item.conclusao_efetiva_data)}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500 text-red-600 font-semibold">Prazo Fatal</label>
                <p className="text-sm font-semibold text-red-600">
                  {formatarData(item.prazo_fatal_data)}
                </p>
              </div>
              {item.cadastro && (
                <div>
                  <label className="text-xs text-gray-500">Data de Cadastro</label>
                  <p className="text-sm">{formatarData(item.cadastro)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Processo */}
          {(item.pasta_proc || item.numero_cnj) && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 flex items-center gap-2 mb-3">
                <Building2 className="h-4 w-4" />
                Processo
              </label>
              <div className="grid grid-cols-2 gap-4">
                {item.pasta_proc && (
                  <div>
                    <label className="text-xs text-gray-500">Pasta</label>
                    <p className="text-sm">{item.pasta_proc}</p>
                  </div>
                )}
                {item.numero_cnj && (
                  <div>
                    <label className="text-xs text-gray-500">Número CNJ</label>
                    <p className="text-sm">{item.numero_cnj}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Cliente/Processo */}
          {item.cliente_processo && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4" />
                Cliente/Processo
              </label>
              <p className="text-sm text-gray-700">{item.cliente_processo}</p>
            </div>
          )}

          {/* Descrição */}
          {item.descricao && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4" />
                Descrição
              </label>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.descricao}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
