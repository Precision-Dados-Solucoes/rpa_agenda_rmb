import { NextRequest, NextResponse } from 'next/server'
import { prisma, testConnection } from '@/lib/prisma'
import { aplicarFiltroSemaforo, detectarCategoriaSemaforo, construirWhereSemaforo } from '@/lib/filtro-semaforo-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/dados
 * Retorna dados da agenda_base com filtros aplicados
 */
export async function GET(request: NextRequest) {
  try {
    // Verificar conexão com o banco antes de processar
    try {
      await prisma.$connect()
    } catch (connectionError) {
      console.error('Erro ao conectar com o banco de dados:', connectionError)
      return NextResponse.json(
        { 
          error: 'Erro de conexão com o banco de dados',
          details: 'O servidor de banco de dados pode estar hibernando ou indisponível. Aguarde alguns instantes e tente novamente.',
          timestamp: new Date().toISOString()
        },
        { status: 503 } // Service Unavailable
      )
    }
    const searchParams = request.nextUrl.searchParams

    // Extrair filtros
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
    
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '100')
    const skip = (page - 1) * limit

    // Construir objeto where para Prisma
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
    console.log('[DEBUG agenda/dados] Permissões obtidas:', permissoes ? {
      role: permissoes.role,
      executantes_count: permissoes.executantes_autorizados?.length || 0,
      executantes: permissoes.executantes_autorizados,
    } : 'null')
    
    // Detectar categoria do semáforo e construir where usando helpers
    const categoriaSemaforo = detectarCategoriaSemaforo(prazoFatalFrom, prazoFatalTo)
    let whereQuery = construirWhereSemaforo(where, categoriaSemaforo)
    
    console.log('[DEBUG agenda/dados] Where antes do filtro de permissões:', JSON.stringify(whereQuery))
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    whereQuery = construirWherePermissoes(permissoes, whereQuery)
    
    console.log('[DEBUG agenda/dados] Where após filtro de permissões:', JSON.stringify(whereQuery))
    
    // Se não for categoria do semáforo, aplicar filtro normal de data
    if (!categoriaSemaforo && (prazoFatalFrom || prazoFatalTo)) {
      whereQuery.prazo_fatal_data = {}
      if (prazoFatalFrom) {
        const dataFrom = new Date(prazoFatalFrom)
        dataFrom.setHours(0, 0, 0, 0)
        whereQuery.prazo_fatal_data.gte = dataFrom
      }
      if (prazoFatalTo) {
        const dataTo = new Date(prazoFatalTo)
        dataTo.setHours(23, 59, 59, 999)
        whereQuery.prazo_fatal_data.lte = dataTo
      }
    }
    
    // Buscar dados (usando select para evitar erro com colunas que podem não existir)
    let dados = await prisma.agendaBase.findMany({
      where: whereQuery,
      orderBy: {
        id_legalone: 'desc',
      },
      select: {
        id_legalone: true,
        compromisso_tarefa: true,
        tipo: true,
        subtipo: true,
        etiqueta: true,
        inicio_data: true,
        inicio_hora: true,
        conclusao_prevista_data: true,
        conclusao_prevista_hora: true,
        conclusao_efetiva_data: true,
        prazo_fatal_data: true,
        pasta_proc: true,
        numero_cnj: true,
        executante: true,
        executante_sim: true,
        descricao: true,
        status: true,
        link: true,
        cadastro: true,
        created_at: true,
        cliente_processo: true,
      },
    })

    // Se for filtro de categoria do semáforo, aplicar a mesma lógica do semáforo
    if (categoriaSemaforo) {
      dados = aplicarFiltroSemaforo(dados, categoriaSemaforo)
    }

    // Aplicar paginação após o filtro
    const total = categoriaSemaforo ? dados.length : await prisma.agendaBase.count({ where: whereQuery })
    const dadosPaginados = dados.slice(skip, skip + limit)

    // Buscar contagem de andamentos para cada item (apenas se houver dados)
    const ids = dadosPaginados.map((d) => d.id_legalone)
    let dadosComAndamentos = dadosPaginados
    if (ids.length > 0) {
      const contagensAndamentos = await prisma.andamentoBase.groupBy({
        by: ['id_agenda_legalone'],
        where: {
          id_agenda_legalone: {
            in: ids,
          },
        },
        _count: {
          id_andamento_legalone: true,
        },
      })

      // Criar mapa de contagens
      const mapaContagens = new Map(
        contagensAndamentos.map((c) => [c.id_agenda_legalone.toString(), c._count.id_andamento_legalone])
      )

      // Adicionar contagem de andamentos aos dados
      dadosComAndamentos = dadosPaginados.map((item) => ({
        ...item,
        quantidadeAndamentos: mapaContagens.get(item.id_legalone.toString()) || 0,
      }))
    } else {
      // Se não houver dados, adicionar quantidadeAndamentos como 0
      dadosComAndamentos = dadosPaginados.map((item) => ({
        ...item,
        quantidadeAndamentos: 0,
      }))
    }

    // Converter BigInt para string para serialização JSON
    const dadosSerializados = dadosComAndamentos.map((item) => {
      const itemSerializado: any = { ...item }
      // Converter id_legalone de BigInt para string
      if (typeof item.id_legalone === 'bigint') {
        itemSerializado.id_legalone = item.id_legalone.toString()
      } else {
        itemSerializado.id_legalone = String(item.id_legalone)
      }
      return itemSerializado
    })

    return NextResponse.json({
      dados: dadosSerializados,
      paginacao: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    })
  } catch (error) {
    console.error('Erro ao buscar dados:', error)
    
    // Detectar tipo de erro para fornecer mensagem mais específica
    let errorMessage = 'Erro ao buscar dados'
    let errorDetails = error instanceof Error ? error.message : String(error)
    
    // Verificar se é erro de conexão com o banco
    if (error instanceof Error) {
      const errorStr = error.message.toLowerCase()
      if (errorStr.includes('connection') || errorStr.includes('connect') || errorStr.includes('timeout')) {
        errorMessage = 'Erro de conexão com o banco de dados'
        errorDetails = 'O servidor pode estar hibernando ou indisponível. Tente novamente em alguns instantes.'
      } else if (errorStr.includes('prisma') || errorStr.includes('database')) {
        errorMessage = 'Erro ao acessar o banco de dados'
        errorDetails = error.message
      }
    }
    
    return NextResponse.json(
      { 
        error: errorMessage, 
        details: errorDetails,
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
  }
}
