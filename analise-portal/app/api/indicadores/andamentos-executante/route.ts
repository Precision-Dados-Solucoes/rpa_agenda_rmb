import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/indicadores/andamentos-executante
 * Retorna contagem total de andamentos por executante
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

    // Construir condições WHERE para SQL de forma segura
    const whereConditions: string[] = ['a.executante IS NOT NULL']
    
    // Adicionar filtro de executantes autorizados se aplicável
    // Verificar se há filtro de permissões primeiro
    if (whereBaseComPermissoes.executante && typeof whereBaseComPermissoes.executante === 'object' && Array.isArray(whereBaseComPermissoes.executante.in)) {
      const executantes = whereBaseComPermissoes.executante.in.map((e: string) => `N'${e.replace(/'/g, "''")}'`).join(', ')
      whereConditions.push(`a.executante IN (${executantes})`)
    } else if (whereBaseComPermissoes.executante && typeof whereBaseComPermissoes.executante === 'string') {
      whereConditions.push(`a.executante = N'${String(whereBaseComPermissoes.executante).replace(/'/g, "''")}'`)
    } else if (whereBase.executante && whereBase.executante !== 'Todos') {
      // Só adicionar filtro de executante do whereBase se não houver filtro de permissões
      whereConditions.push(`a.executante = N'${whereBase.executante.replace(/'/g, "''")}'`)
    }
    if (whereBase.status) {
      whereConditions.push(`a.status = N'${whereBase.status.replace(/'/g, "''")}'`)
    }
    if (whereBase.etiqueta) {
      whereConditions.push(`a.etiqueta = N'${whereBase.etiqueta.replace(/'/g, "''")}'`)
    }
    if (whereBase.subtipo) {
      whereConditions.push(`a.subtipo = N'${whereBase.subtipo.replace(/'/g, "''")}'`)
    }
    if (whereBase.pasta_proc) {
      whereConditions.push(`a.pasta_proc = N'${whereBase.pasta_proc.replace(/'/g, "''")}'`)
    }
    if (whereBase.inicio_data) {
      if (whereBase.inicio_data.gte) {
        whereConditions.push(`a.inicio_data >= '${whereBase.inicio_data.gte.toISOString().split('T')[0]}'`)
      }
      if (whereBase.inicio_data.lte) {
        whereConditions.push(`a.inicio_data <= '${whereBase.inicio_data.lte.toISOString().split('T')[0]}'`)
      }
    }
    if (whereBase.conclusao_prevista_data) {
      if (whereBase.conclusao_prevista_data.gte) {
        whereConditions.push(`a.conclusao_prevista_data >= '${whereBase.conclusao_prevista_data.gte.toISOString().split('T')[0]}'`)
      }
      if (whereBase.conclusao_prevista_data.lte) {
        whereConditions.push(`a.conclusao_prevista_data <= '${whereBase.conclusao_prevista_data.lte.toISOString().split('T')[0]}'`)
      }
    }
    if (whereBase.conclusao_efetiva_data) {
      if (whereBase.conclusao_efetiva_data.gte) {
        whereConditions.push(`a.conclusao_efetiva_data >= '${whereBase.conclusao_efetiva_data.gte.toISOString().split('T')[0]}'`)
      }
      if (whereBase.conclusao_efetiva_data.lte) {
        whereConditions.push(`a.conclusao_efetiva_data <= '${whereBase.conclusao_efetiva_data.lte.toISOString().split('T')[0]}'`)
      }
    }
    if (whereBase.prazo_fatal_data) {
      if (whereBase.prazo_fatal_data.gte) {
        whereConditions.push(`a.prazo_fatal_data >= '${whereBase.prazo_fatal_data.gte.toISOString().split('T')[0]}'`)
      }
      if (whereBase.prazo_fatal_data.lte) {
        whereConditions.push(`a.prazo_fatal_data <= '${whereBase.prazo_fatal_data.lte.toISOString().split('T')[0]}'`)
      }
    }

    const whereClause = `WHERE ${whereConditions.join(' AND ')}`

    // Usar SQL raw para fazer JOIN e agrupamento diretamente no banco
    const query = `
      SELECT 
        a.executante,
        COUNT(an.id_andamento_legalone) as quantidade
      FROM andamento_base an
      INNER JOIN agenda_base a ON an.id_agenda_legalone = a.id_legalone
      ${whereClause}
      GROUP BY a.executante
      ORDER BY quantidade DESC
    `

    const result = await prisma.$queryRawUnsafe<Array<{ executante: string; quantidade: bigint }>>(query)

    // Converter para array
    const dados = result
      .map((row) => ({
        executante: row.executante || '(Em branco)',
        quantidade: Number(row.quantidade),
      }))

    return NextResponse.json({
      dados,
      total: dados.reduce((sum, item) => sum + item.quantidade, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados de andamentos por executante:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar dados de andamentos por executante',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
