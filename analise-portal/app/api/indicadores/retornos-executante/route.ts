import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/indicadores/retornos-executante
 * Retorna contagem de andamentos tipo "6. Retornado" por executante
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Obter permissões do usuário para aplicar filtro de executantes
    const permissoes = await obterPermissoesUsuario(request)
    
    // Construir where base usando o helper
    const whereBase = construirWhere(searchParams)
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    const whereBaseComPermissoes = construirWherePermissoes(permissoes, whereBase)

    // Buscar andamentos do tipo "6. Retornado"
    const andamentos = await prisma.andamentoBase.findMany({
      where: {
        tipo_andamento: '6. Retornado',
      },
      select: {
        id_agenda_legalone: true,
      },
    })

    const idsAgenda = new Set(andamentos.map((a) => a.id_agenda_legalone.toString()))

    if (idsAgenda.size === 0) {
      return NextResponse.json({
        dados: [],
        total: 0,
      })
    }

    // Construir where final, evitando conflito entre filtro de permissões e not: null
    const whereFinal: any = {
      ...whereBaseComPermissoes,
      id_legalone: {
        in: Array.from(idsAgenda).map((id) => BigInt(id)),
      },
    }
    
    // Se não houver filtro de executante aplicado, adicionar "not: null"
    // Se já houver filtro "in", o Prisma já vai filtrar apenas os valores na lista
    if (!whereBaseComPermissoes.executante) {
      whereFinal.executante = { not: null }
    } else if (whereBaseComPermissoes.executante && typeof whereBaseComPermissoes.executante === 'object' && whereBaseComPermissoes.executante.in) {
      // Se tem filtro "in", manter apenas esse (os valores na lista já não incluem null)
      whereFinal.executante = whereBaseComPermissoes.executante
    } else if (typeof whereBaseComPermissoes.executante === 'string') {
      // Se é string específica, manter
      whereFinal.executante = whereBaseComPermissoes.executante
    }
    
    // Helper para serializar objetos com BigInt
    const serializeForLog = (obj: any): any => {
      if (obj === null || obj === undefined) return obj
      if (typeof obj === 'bigint') return obj.toString()
      if (Array.isArray(obj)) return obj.map(serializeForLog)
      if (typeof obj === 'object') {
        const result: any = {}
        for (const key in obj) {
          result[key] = serializeForLog(obj[key])
        }
        return result
      }
      return obj
    }

    console.log('[DEBUG retornos-executante]', serializeForLog({
      permissoes: permissoes ? {
        role: permissoes.role,
        executantes_count: permissoes.executantes_autorizados?.length || 0,
        executantes: permissoes.executantes_autorizados,
      } : null,
      whereBase: whereBase,
      whereBaseComPermissoes: whereBaseComPermissoes,
      whereFinal: whereFinal,
      totalAndamentosInicial: andamentos.length,
      idsAgendaSize: idsAgenda.size,
      idsAgendaSample: Array.from(idsAgenda).slice(0, 5),
    }))
    
    // Buscar agendas que correspondem aos andamentos e aplicar filtros
    const agendas = await prisma.agendaBase.findMany({
      where: whereFinal,
      select: {
        id_legalone: true,
        executante: true,
      },
    })

    console.log('[DEBUG retornos-executante] Após buscar agendas:', {
      totalAgendasEncontradas: agendas.length,
      agendasSample: agendas.slice(0, 3).map(a => ({
        id: a.id_legalone.toString(),
        executante: a.executante,
      })),
    })

    // Criar conjunto de IDs de agendas que passaram no filtro de permissões
    const idsAgendasFiltradas = new Set(agendas.map((a) => a.id_legalone.toString()))
    
    // Criar mapa de id_agenda -> executante apenas para agendas filtradas
    const mapaAgendaExecutante = new Map<string, string>()
    agendas.forEach((agenda) => {
      const id = agenda.id_legalone.toString()
      const executante = agenda.executante || '(Em branco)'
      mapaAgendaExecutante.set(id, executante)
    })

    // Agrupar andamentos por executante
    // IMPORTANTE: Filtrar apenas andamentos cujas agendas passaram no filtro de permissões
    const agrupado = new Map<string, number>()

    andamentos.forEach((andamento) => {
      const idAgenda = andamento.id_agenda_legalone.toString()
      // Só processar se a agenda estiver no conjunto de agendas filtradas
      if (idsAgendasFiltradas.has(idAgenda)) {
        const executante = mapaAgendaExecutante.get(idAgenda)
        if (executante) {
          agrupado.set(executante, (agrupado.get(executante) || 0) + 1)
        }
      }
    })
    
    console.log('[DEBUG retornos-executante] Resultado final:', {
      totalAndamentos: andamentos.length,
      totalAgendasFiltradas: agendas.length,
      idsAgendasFiltradas: Array.from(idsAgendasFiltradas).slice(0, 5), // Primeiros 5 para debug
      agrupadoSize: agrupado.size,
      dadosFinal: Array.from(agrupado.entries()).slice(0, 3), // Primeiros 3 para debug
    })

    // Converter para array e ordenar
    const dados = Array.from(agrupado.entries())
      .map(([executante, quantidade]) => ({
        executante,
        quantidade,
      }))
      .sort((a, b) => b.quantidade - a.quantidade)

    return NextResponse.json({
      dados,
      total: dados.reduce((sum, item) => sum + item.quantidade, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados de retornos por executante:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar dados de retornos por executante',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
