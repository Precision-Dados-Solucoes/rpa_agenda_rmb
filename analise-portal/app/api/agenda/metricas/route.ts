import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/metricas
 * Retorna métricas gerais da agenda
 * Aplica os mesmos filtros da API de dados (exceto os específicos de cada métrica)
 */
export async function GET(request: NextRequest) {
  try {
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

    // Construir objeto where base para aplicar em todas as métricas
    const whereBase: any = {}

    if (executante && executante !== 'Todos') {
      whereBase.executante = executante
    }

    if (status && status !== 'Todos') {
      whereBase.status = status
    }

    if (complexidade && complexidade !== 'Todos') {
      whereBase.etiqueta = complexidade
    }

    if (tipo && tipo !== 'Todos') {
      whereBase.subtipo = tipo
    }

    if (pasta && pasta !== 'Todos') {
      whereBase.pasta_proc = pasta
    }

    if (dataInicioFrom || dataInicioTo) {
      whereBase.inicio_data = {}
      if (dataInicioFrom) {
        whereBase.inicio_data.gte = new Date(dataInicioFrom)
      }
      if (dataInicioTo) {
        whereBase.inicio_data.lte = new Date(dataInicioTo)
      }
    }

    if (conclusaoPrevistaFrom || conclusaoPrevistaTo) {
      whereBase.conclusao_prevista_data = {}
      if (conclusaoPrevistaFrom) {
        whereBase.conclusao_prevista_data.gte = new Date(conclusaoPrevistaFrom)
      }
      if (conclusaoPrevistaTo) {
        whereBase.conclusao_prevista_data.lte = new Date(conclusaoPrevistaTo)
      }
    }

    if (conclusaoEfetivaFrom || conclusaoEfetivaTo) {
      whereBase.conclusao_efetiva_data = {}
      if (conclusaoEfetivaFrom) {
        whereBase.conclusao_efetiva_data.gte = new Date(conclusaoEfetivaFrom)
      }
      if (conclusaoEfetivaTo) {
        whereBase.conclusao_efetiva_data.lte = new Date(conclusaoEfetivaTo)
      }
    }

    // Obter permissões do usuário para aplicar filtro de executantes
    const permissoes = await obterPermissoesUsuario(request)
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    const whereBaseComPermissoes = construirWherePermissoes(permissoes, whereBase)
    
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)
    const amanha = new Date(hoje)
    amanha.setDate(amanha.getDate() + 1)

    const ontem = new Date(hoje)
    ontem.setDate(ontem.getDate() - 1)

    // 1. Compromissos: COUNT DISTINCT id_legalone WHERE compromisso_tarefa = 'Compromisso'
    const compromissosResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        compromisso_tarefa: 'Compromisso',
      },
      select: {
        id_legalone: true,
      },
    })
    const compromissos = new Set(compromissosResult.map((c) => c.id_legalone.toString())).size

    // 2. Tarefas: COUNT DISTINCT id_legalone WHERE compromisso_tarefa = 'Tarefa'
    const tarefasResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        compromisso_tarefa: 'Tarefa',
      },
      select: {
        id_legalone: true,
      },
    })
    const tarefas = new Set(tarefasResult.map((t) => t.id_legalone.toString())).size

    // 3. Hoje: COUNT DISTINCT id_legalone WHERE inicio_data = TODAY()
    const hojeResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        inicio_data: {
          gte: hoje,
          lt: amanha,
        },
      },
      select: {
        id_legalone: true,
      },
    })
    const hojeCount = new Set(hojeResult.map((h) => h.id_legalone.toString())).size

    // 4. Atrasados: Lógica complexa
    // Buscar compromissos de ontem com status Pendente
    const compromissosOntem = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        inicio_data: {
          gte: ontem,
          lt: hoje,
        },
        status: 'Pendente',
      },
      select: {
        id_legalone: true,
      },
    })

    const idsCompromissosOntem = new Set(
      compromissosOntem.map((c) => c.id_legalone.toString())
    )

    // Buscar IDs que têm andamento tipo "1. Produzido" ou "7. (Re) Produzido"
    const andamentosTipo37 = await prisma.$queryRawUnsafe<Array<{ id_agenda_legalone: bigint }>>(
      `SELECT DISTINCT id_agenda_legalone 
       FROM andamento_base 
       WHERE tipo_andamento IN ('1. Produzido', '7. (Re) Produzido')`
    )

    const idsComAndamento = new Set(
      andamentosTipo37.map((a) => a.id_agenda_legalone.toString())
    )

    // IDs que estão em compromissosOntem mas NÃO estão em idsComAndamento
    const atrasados = Array.from(idsCompromissosOntem).filter(
      (id) => !idsComAndamento.has(id)
    ).length

    // 5. Em conferência: Itens pendentes que têm andamento tipo "1. Produzido" ou "7. (Re) Produzido"
    const itensPendentes = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        status: 'Pendente',
      },
      select: {
        id_legalone: true,
      },
    })

    const idsPendentes = new Set(
      itensPendentes.map((i) => i.id_legalone.toString())
    )

    // Intersecção: IDs que estão em pendentes E têm andamento tipo 1 ou 7
    const emConferencia = Array.from(idsPendentes).filter((id) =>
      idsComAndamento.has(id)
    ).length

    // 6. Fatal: COUNT DISTINCT id_legalone WHERE prazo_fatal_data = TODAY()
    const fatalResult = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
        prazo_fatal_data: {
          gte: hoje,
          lt: amanha,
        },
      },
      select: {
        id_legalone: true,
      },
    })
    const fatal = new Set(fatalResult.map((f) => f.id_legalone.toString())).size

    return NextResponse.json({
      compromissos,
      tarefas,
      hoje: hojeCount,
      atrasados,
      emConferencia,
      fatal,
    })
  } catch (error) {
    console.error('Erro ao buscar métricas:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar métricas',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
