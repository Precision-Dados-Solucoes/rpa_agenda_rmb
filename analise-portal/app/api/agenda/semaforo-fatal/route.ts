import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/agenda/semaforo-fatal
 * Retorna contagem de registros por categoria do semáforo do fatal
 * Aplica os mesmos filtros da API de dados (exceto prazo_fatal)
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Extrair filtros (exceto prazo_fatal que será calculado)
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
    
    // Aplicar filtro de executantes autorizados (se não for administrador)
    const whereComPermissoes = construirWherePermissoes(permissoes, where)
    
    // Buscar todos os registros com prazo_fatal_data (incluindo id_legalone para contar únicos)
    const registros = await prisma.agendaBase.findMany({
      where: {
        ...whereComPermissoes,
        prazo_fatal_data: {
          not: null,
        },
      },
      select: {
        id_legalone: true,
        prazo_fatal_data: true,
      },
    })

    // Calcular dias até o prazo fatal e classificar (contando id_legalone únicos)
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)

    const dataLimitePossivelPerda = new Date('2026-01-01')
    dataLimitePossivelPerda.setHours(0, 0, 0, 0)

    const categorias = {
      'Possível perda': new Set<string>(),
      'Crítico': new Set<string>(),
      'Atenção': new Set<string>(),
      'Próximo': new Set<string>(),
      'Normal': new Set<string>(),
    }

    registros.forEach((registro) => {
      if (!registro.prazo_fatal_data) return

      const prazoFatal = new Date(registro.prazo_fatal_data)
      prazoFatal.setHours(0, 0, 0, 0)

      // Calcular diferença em dias
      const diffTime = prazoFatal.getTime() - hoje.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const id = registro.id_legalone.toString()

      // Classificar (usando Set para contar id_legalone únicos)
      if (diffDays < 0 && prazoFatal >= dataLimitePossivelPerda) {
        categorias['Possível perda'].add(id)
      } else if (diffDays === 0) {
        categorias['Crítico'].add(id)
      } else if (diffDays === 1 || diffDays === 2) {
        categorias['Atenção'].add(id)
      } else if (diffDays >= 3 && diffDays <= 5) {
        categorias['Próximo'].add(id)
      } else if (diffDays >= 6) {
        categorias['Normal'].add(id)
      }
    })

    // Formatar resultado (contando tamanho dos Sets)
    const resultado = [
      {
        categoria: 'Possível perda',
        quantidade: categorias['Possível perda'].size,
        cor: '#ec4899', // pink
        ordem: 0,
      },
      {
        categoria: 'Crítico',
        quantidade: categorias['Crítico'].size,
        cor: '#ef4444', // red
        ordem: 1,
      },
      {
        categoria: 'Atenção',
        quantidade: categorias['Atenção'].size,
        cor: '#eab308', // yellow
        ordem: 2,
      },
      {
        categoria: 'Próximo',
        quantidade: categorias['Próximo'].size,
        cor: '#3b82f6', // blue
        ordem: 3,
      },
      {
        categoria: 'Normal',
        quantidade: categorias['Normal'].size,
        cor: '#22c55e', // green
        ordem: 4,
      },
    ]

    return NextResponse.json({
      dados: resultado,
      total: Array.from(Object.values(categorias)).reduce((sum, set) => sum + set.size, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados do semáforo:', error)
    return NextResponse.json(
      { 
        error: 'Erro ao buscar dados do semáforo', 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    )
  }
}
