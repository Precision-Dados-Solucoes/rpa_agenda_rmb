import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'

/**
 * GET /api/indicadores
 * Retorna os indicadores de performance:
 * - Agendas: total de id_legalone únicos
 * - Produzidos: id_legalone únicos com último andamento "1. Produzido" ou "7. (Re) Produzido"
 * - Antecipado: cadastro_andamento < inicio_data
 * - No prazo: cadastro_andamento = inicio_data
 * - Tardio: cadastro_andamento > inicio_data
 * - Cumprido: status = 'Cumprido'
 * - Com parecer: status = 'Cumprido com parecer'
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Construir where base usando o helper
    const whereBase = construirWhere(searchParams)

    // 1. AGENDAS: Conta id_legalone únicos na agenda_base
    const agendasResult = await prisma.agendaBase.findMany({
      where: whereBase,
      select: {
        id_legalone: true,
      },
    })
    const agendas = new Set(agendasResult.map((a) => a.id_legalone.toString())).size

    // 2. PRODUZIDOS: Lógica complexa
    // Buscar todos os andamentos tipo "1. Produzido" ou "7. (Re) Produzido"
    // Para cada id_agenda_legalone, pegar o último andamento relevante
    // Se tiver "7. (Re) Produzido" depois de "1. Produzido", considerar apenas o "7. (Re) Produzido"
    
    // Primeiro, buscar todos os andamentos relevantes ordenados por data
    const andamentosRelevantes = await prisma.andamentoBase.findMany({
      where: {
        tipo_andamento: {
          in: ['1. Produzido', '7. (Re) Produzido'],
        },
      },
      select: {
        id_agenda_legalone: true,
        tipo_andamento: true,
        cadastro_andamento: true,
      },
      orderBy: [
        { id_agenda_legalone: 'asc' },
        { cadastro_andamento: 'asc' },
      ],
    })

    // Agrupar por id_agenda_legalone
    // Para cada id, se houver "7. (Re) Produzido", usar ele (o mais recente)
    // Caso contrário, usar o último "1. Produzido"
    const andamentosPorAgenda = new Map<string, Array<{ tipo: string; data: Date | null }>>()
    
    for (const andamento of andamentosRelevantes) {
      const idAgenda = andamento.id_agenda_legalone.toString()
      const tipo = andamento.tipo_andamento || ''
      const data = andamento.cadastro_andamento

      if (!andamentosPorAgenda.has(idAgenda)) {
        andamentosPorAgenda.set(idAgenda, [])
      }
      andamentosPorAgenda.get(idAgenda)!.push({ tipo, data })
    }

    // Para cada id_agenda_legalone, determinar o andamento relevante
    const ultimosAndamentos = new Map<string, { tipo: string; data: Date | null }>()
    
    for (const [idAgenda, andamentos] of andamentosPorAgenda.entries()) {
      // Verificar se há algum "7. (Re) Produzido"
      const reProduzidos = andamentos.filter((a) => a.tipo === '7. (Re) Produzido')
      
      if (reProduzidos.length > 0) {
        // Se houver "7. (Re) Produzido", usar o mais recente
        const maisRecente = reProduzidos.reduce((prev, curr) => {
          if (!prev.data) return curr
          if (!curr.data) return prev
          return curr.data > prev.data ? curr : prev
        })
        ultimosAndamentos.set(idAgenda, maisRecente)
      } else {
        // Se não houver "7. (Re) Produzido", usar o último "1. Produzido"
        const produzidos = andamentos.filter((a) => a.tipo === '1. Produzido')
        if (produzidos.length > 0) {
          const maisRecente = produzidos.reduce((prev, curr) => {
            if (!prev.data) return curr
            if (!curr.data) return prev
            return curr.data > prev.data ? curr : prev
          })
          ultimosAndamentos.set(idAgenda, maisRecente)
        }
      }
    }

    const idsProduzidos = new Set(ultimosAndamentos.keys())
    
    // Aplicar filtros da agenda_base aos IDs produzidos
    const agendasFiltradas = await prisma.agendaBase.findMany({
      where: whereBase,
      select: {
        id_legalone: true,
      },
    })
    
    const idsAgendasFiltradas = new Set(agendasFiltradas.map((a) => a.id_legalone.toString()))
    
    // Intersecção: IDs que estão em ambos (produzidos E filtrados)
    const produzidos = Array.from(idsProduzidos).filter((id) => idsAgendasFiltradas.has(id)).length

    // 3. ANTECIPADO, NO PRAZO, TARDIO
    // Para cada id_agenda_legalone com andamento relevante, comparar cadastro_andamento com inicio_data
    const agendasComInicio = await prisma.agendaBase.findMany({
      where: {
        ...whereBase,
        inicio_data: {
          not: null,
        },
      },
      select: {
        id_legalone: true,
        inicio_data: true,
      },
    })

    const mapAgendaInicio = new Map<string, Date>()
    for (const agenda of agendasComInicio) {
      if (agenda.inicio_data) {
        mapAgendaInicio.set(agenda.id_legalone.toString(), agenda.inicio_data)
      }
    }

    let antecipado = 0
    let noPrazo = 0
    let tardio = 0

    for (const [idAgenda, andamentoInfo] of ultimosAndamentos.entries()) {
      // Verificar se o id_agenda está nos filtros aplicados
      if (!idsAgendasFiltradas.has(idAgenda)) continue

      const inicioData = mapAgendaInicio.get(idAgenda)
      if (!inicioData || !andamentoInfo.data) continue

      // Normalizar datas para comparação (apenas data, sem hora)
      const dataInicio = new Date(inicioData)
      dataInicio.setHours(0, 0, 0, 0)
      
      const dataAndamento = new Date(andamentoInfo.data)
      dataAndamento.setHours(0, 0, 0, 0)

      if (dataAndamento < dataInicio) {
        antecipado++
      } else if (dataAndamento.getTime() === dataInicio.getTime()) {
        noPrazo++
      } else {
        tardio++
      }
    }

    // 4. CUMPRIDO: status = 'Cumprido'
    const cumpridoResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBase,
        status: 'Cumprido',
      },
      select: {
        id_legalone: true,
      },
    })
    const cumprido = new Set(cumpridoResult.map((c) => c.id_legalone.toString())).size

    // 5. COM PARECER: status = 'Cumprido com parecer'
    const comParecerResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBase,
        status: 'Cumprido com parecer',
      },
      select: {
        id_legalone: true,
      },
    })
    const comParecer = new Set(comParecerResult.map((c) => c.id_legalone.toString())).size

    return NextResponse.json({
      agendas,
      produzidos,
      antecipado,
      noPrazo,
      tardio,
      cumprido,
      comParecer,
    })
  } catch (error) {
    console.error('Erro ao buscar indicadores:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar indicadores',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
