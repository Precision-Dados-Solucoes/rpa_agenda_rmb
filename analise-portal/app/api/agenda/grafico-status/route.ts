import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { aplicarFiltroSemaforo, detectarCategoriaSemaforo, construirWhereSemaforo } from '@/lib/filtro-semaforo-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/grafico-status
 * Retorna contagem de id_legalone únicos por status
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const prazoFatalFrom = searchParams.get('prazoFatalFrom')
    const prazoFatalTo = searchParams.get('prazoFatalTo')
    
    // Obter permissões do usuário para aplicar filtro de executantes
    const permissoes = await obterPermissoesUsuario(request)
    
    let where = construirWhere(searchParams)
    const categoriaSemaforo = detectarCategoriaSemaforo(prazoFatalFrom, prazoFatalTo)
    where = construirWhereSemaforo(where, categoriaSemaforo)
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    where = construirWherePermissoes(permissoes, where)

    // Buscar todos os registros que atendem aos filtros
    let registros = await prisma.agendaBase.findMany({
      where: {
        ...where,
        status: {
          not: null,
        },
      },
      select: {
        id_legalone: true,
        status: true,
        prazo_fatal_data: true,
      },
    })

    // Aplicar filtro do semáforo em memória se necessário
    if (categoriaSemaforo) {
      registros = aplicarFiltroSemaforo(registros, categoriaSemaforo)
    }

    // Agrupar por status e contar id_legalone únicos
    const agrupado = new Map<string, Set<string>>()
    
    registros.forEach((registro) => {
      const status = registro.status || '(Em branco)'
      const id = registro.id_legalone.toString()
      
      if (!agrupado.has(status)) {
        agrupado.set(status, new Set())
      }
      agrupado.get(status)!.add(id)
    })

    // Converter para array e ordenar
    const dadosFormatados = Array.from(agrupado.entries())
      .map(([status, ids]) => ({
        status,
        quantidade: ids.size,
      }))
      .sort((a, b) => b.quantidade - a.quantidade)

    return NextResponse.json({
      dados: dadosFormatados.sort((a, b) => b.quantidade - a.quantidade),
    })
  } catch (error) {
    console.error('Erro ao buscar dados do gráfico de status:', error)
    return NextResponse.json(
      { error: 'Erro ao buscar dados', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
