import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { aplicarFiltroSemaforo, detectarCategoriaSemaforo, construirWhereSemaforo } from '@/lib/filtro-semaforo-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/grafico-complexidade
 * Retorna contagem de id_legalone únicos por etiqueta (complexidade)
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
        etiqueta: {
          not: null,
        },
      },
      select: {
        id_legalone: true,
        etiqueta: true,
        prazo_fatal_data: true,
      },
    })

    // Aplicar filtro do semáforo em memória se necessário
    if (categoriaSemaforo) {
      registros = aplicarFiltroSemaforo(registros, categoriaSemaforo)
    }

    // Agrupar por etiqueta e contar id_legalone únicos
    const agrupado = new Map<string, Set<string>>()
    
    registros.forEach((registro) => {
      const etiqueta = registro.etiqueta || '(Em branco)'
      const id = registro.id_legalone.toString()
      
      if (!agrupado.has(etiqueta)) {
        agrupado.set(etiqueta, new Set())
      }
      agrupado.get(etiqueta)!.add(id)
    })

    // Converter para array, filtrar apenas as 3 categorias e ordenar
    // Nota: Os valores no banco são "Alta Complexidade", "Média Complexidade", "Baixa Complexidade" (com C maiúsculo)
    const categoriasPermitidas = ['Alta Complexidade', 'Média Complexidade', 'Baixa Complexidade']
    const dadosFormatados = Array.from(agrupado.entries())
      .filter(([complexidade]) => categoriasPermitidas.includes(complexidade))
      .map(([complexidade, ids]) => ({
        complexidade,
        quantidade: ids.size,
      }))
      .sort((a, b) => {
        // Ordenar: Alta, Média, Baixa
        const ordem = { 'Alta Complexidade': 0, 'Média Complexidade': 1, 'Baixa Complexidade': 2 }
        return (ordem[a.complexidade as keyof typeof ordem] ?? 999) - (ordem[b.complexidade as keyof typeof ordem] ?? 999)
      })

    return NextResponse.json({
      dados: dadosFormatados,
    })
  } catch (error) {
    console.error('Erro ao buscar dados do gráfico de complexidade:', error)
    return NextResponse.json(
      { error: 'Erro ao buscar dados', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    )
  }
}
