import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { aplicarFiltroSemaforo, detectarCategoriaSemaforo, construirWhereSemaforo } from '@/lib/filtro-semaforo-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/grafico-executante
 * Retorna contagem de id_legalone únicos por executante
 * Aplica os mesmos filtros da API de dados
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Extrair filtros (mesmos da API de dados)
    const executante = searchParams.get('executante')
    const status = searchParams.get('status')
    const complexidade = searchParams.get('complexidade')
    const tipo = searchParams.get('tipo')
    const pasta = searchParams.get('pasta')
    
    const dataInicioFrom = searchParams.get('dataInicioFrom')
    const dataInicioTo = searchParams.get('dataInicioTo')
    const conclusaoPrevistaFrom = searchParams.get('conclusaoPrevistaFrom')
    const conclusaoPrevistaTo = searchParams.get('conclusaoPrevistaTo')
    const conclusaoEfetivaFrom = searchParams.get('conclusaoEfetivaFrom')
    const conclusaoEfetivaTo = searchParams.get('conclusaoEfetivaTo')
    const prazoFatalFrom = searchParams.get('prazoFatalFrom')
    const prazoFatalTo = searchParams.get('prazoFatalTo')

    // Construir objeto where para Prisma (mesmo da API de dados)
    const where: any = {}

    if (executante && executante !== 'Todos') {
      where.executante = executante
    }

    if (status && status !== 'Todos') {
      where.status = status
    }

    if (complexidade && complexidade !== 'Todos') {
      where.etiqueta = complexidade
    }

    if (tipo && tipo !== 'Todos') {
      where.subtipo = tipo
    }

    if (pasta && pasta !== 'Todos') {
      where.pasta_proc = pasta
    }

    if (dataInicioFrom || dataInicioTo) {
      where.inicio_data = {}
      if (dataInicioFrom) {
        where.inicio_data.gte = new Date(dataInicioFrom)
      }
      if (dataInicioTo) {
        where.inicio_data.lte = new Date(dataInicioTo)
      }
    }

    if (conclusaoPrevistaFrom || conclusaoPrevistaTo) {
      where.conclusao_prevista_data = {}
      if (conclusaoPrevistaFrom) {
        where.conclusao_prevista_data.gte = new Date(conclusaoPrevistaFrom)
      }
      if (conclusaoPrevistaTo) {
        where.conclusao_prevista_data.lte = new Date(conclusaoPrevistaTo)
      }
    }

    if (conclusaoEfetivaFrom || conclusaoEfetivaTo) {
      where.conclusao_efetiva_data = {}
      if (conclusaoEfetivaFrom) {
        where.conclusao_efetiva_data.gte = new Date(conclusaoEfetivaFrom)
      }
      if (conclusaoEfetivaTo) {
        where.conclusao_efetiva_data.lte = new Date(conclusaoEfetivaTo)
      }
    }

    // Obter permissões do usuário para aplicar filtro de executantes
    const permissoes = await obterPermissoesUsuario(request)
    
    // Detectar categoria do semáforo e construir where
    const categoriaSemaforo = detectarCategoriaSemaforo(prazoFatalFrom, prazoFatalTo)
    let whereQuery = construirWhereSemaforo(where, categoriaSemaforo)
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    whereQuery = construirWherePermissoes(permissoes, whereQuery)

    console.log('[DEBUG grafico-executante]', {
      prazoFatalFrom,
      prazoFatalTo,
      categoriaSemaforo,
      whereQueryPrazoFatal: whereQuery.prazo_fatal_data,
    })

    // Buscar todos os registros
    // Nota: whereQuery já contém o filtro de executantes autorizados
    // O Prisma não permite executante: { in: [...], not: null } ao mesmo tempo
    // Então vamos filtrar nulls depois, ou garantir que o filtro "in" já exclui nulls
    const whereFinal: any = { ...whereQuery }
    
    // Se não houver filtro de executante aplicado, adicionar "not: null"
    // Se já houver filtro "in", o Prisma já vai filtrar apenas os valores na lista
    if (!whereQuery.executante) {
      whereFinal.executante = { not: null }
    } else if (whereQuery.executante && typeof whereQuery.executante === 'object' && whereQuery.executante.in) {
      // Se tem filtro "in", manter apenas esse (os valores na lista já não incluem null)
      whereFinal.executante = whereQuery.executante
    } else if (typeof whereQuery.executante === 'string') {
      // Se é string específica, manter
      whereFinal.executante = whereQuery.executante
    }
    
    console.log('[DEBUG grafico-executante] Where final antes da query:', JSON.stringify(whereFinal))
    
    const registros = await prisma.agendaBase.findMany({
      where: whereFinal,
      select: {
        id_legalone: true,
        executante: true,
        prazo_fatal_data: true,
      },
    })

    console.log('[DEBUG grafico-executante] Total registros antes do filtro:', registros.length)

    // Aplicar filtro do semáforo em memória se necessário
    const registrosFiltrados = categoriaSemaforo 
      ? aplicarFiltroSemaforo(registros, categoriaSemaforo)
      : registros

    console.log('[DEBUG grafico-executante] Total registros após filtro:', registrosFiltrados.length)

    // Agrupar por executante e contar id_legalone únicos
    const agrupado = new Map<string, Set<string>>()
    
    registrosFiltrados.forEach((registro) => {
      const executante = registro.executante || '(Em branco)'
      const id = registro.id_legalone.toString()
      
      if (!agrupado.has(executante)) {
        agrupado.set(executante, new Set())
      }
      agrupado.get(executante)!.add(id)
    })

    // Converter para array e ordenar
    const dados = Array.from(agrupado.entries())
      .map(([executante, ids]) => ({
        executante,
        quantidade: ids.size,
      }))
      .sort((a, b) => b.quantidade - a.quantidade)

    return NextResponse.json({
      dados,
      total: dados.reduce((sum, item) => sum + item.quantidade, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados do gráfico:', error)
    return NextResponse.json(
      { 
        error: 'Erro ao buscar dados do gráfico', 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    )
  }
}
