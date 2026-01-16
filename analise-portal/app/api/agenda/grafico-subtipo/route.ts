import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { aplicarFiltroSemaforo, detectarCategoriaSemaforo, construirWhereSemaforo } from '@/lib/filtro-semaforo-helper'

/**
 * GET /api/agenda/grafico-subtipo
 * Retorna contagem de id_legalone únicos por subtipo
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const prazoFatalFrom = searchParams.get('prazoFatalFrom')
    const prazoFatalTo = searchParams.get('prazoFatalTo')
    
    let where = construirWhere(searchParams)
    const categoriaSemaforo = detectarCategoriaSemaforo(prazoFatalFrom, prazoFatalTo)
    where = construirWhereSemaforo(where, categoriaSemaforo)

    // Buscar todos os registros que atendem aos filtros
    let registros = await prisma.agendaBase.findMany({
      where: {
        ...where,
        subtipo: {
          not: null,
        },
      },
      select: {
        id_legalone: true,
        subtipo: true,
        prazo_fatal_data: true,
      },
    })

    // Aplicar filtro do semáforo em memória se necessário
    if (categoriaSemaforo) {
      registros = aplicarFiltroSemaforo(registros, categoriaSemaforo)
    }

    // Agrupar por subtipo e contar id_legalone únicos
    const agrupado = new Map<string, Set<string>>()
    
    registros.forEach((registro) => {
      const subtipo = registro.subtipo || '(Em branco)'
      const id = registro.id_legalone.toString()
      
      if (!agrupado.has(subtipo)) {
        agrupado.set(subtipo, new Set())
      }
      agrupado.get(subtipo)!.add(id)
    })

    // Converter para array e ordenar
    const dadosFormatados = Array.from(agrupado.entries())
      .map(([subtipo, ids]) => ({
        subtipo,
        quantidade: ids.size,
      }))
      .sort((a, b) => b.quantidade - a.quantidade)

    return NextResponse.json({
      dados: dadosFormatados.sort((a, b) => b.quantidade - a.quantidade),
    })
  } catch (error) {
    console.error('Erro ao buscar dados do gráfico de subtipo:', error)
    return NextResponse.json(
      { error: 'Erro ao buscar dados', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
