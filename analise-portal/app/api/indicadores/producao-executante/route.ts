import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/indicadores/producao-executante
 * Retorna contagem de id_legalone únicos por executante
 * Separado por status: "Cumprido" e "Cumprido com parecer"
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

    // Construir where final, evitando conflito entre filtro de permissões e not: null
    const whereFinal: any = {
      ...whereBaseComPermissoes,
      status: {
        in: ['Cumprido', 'Cumprido com parecer'],
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
    
    console.log('[DEBUG producao-executante] Where final:', JSON.stringify(whereFinal))
    
    // Buscar registros com status "Cumprido" ou "Cumprido com parecer"
    const registros = await prisma.agendaBase.findMany({
      where: whereFinal,
      select: {
        id_legalone: true,
        executante: true,
        status: true,
      },
    })

    // Agrupar por executante e status, contando id_legalone únicos
    const agrupado = new Map<string, { cumprido: Set<string>; comParecer: Set<string> }>()
    
    registros.forEach((registro) => {
      const executante = registro.executante || '(Em branco)'
      const id = registro.id_legalone.toString()
      
      if (!agrupado.has(executante)) {
        agrupado.set(executante, {
          cumprido: new Set(),
          comParecer: new Set(),
        })
      }
      
      const grupo = agrupado.get(executante)!
      if (registro.status === 'Cumprido') {
        grupo.cumprido.add(id)
      } else if (registro.status === 'Cumprido com parecer') {
        grupo.comParecer.add(id)
      }
    })

    // Converter para array e calcular totais
    const dados = Array.from(agrupado.entries())
      .map(([executante, grupos]) => {
        const cumprido = grupos.cumprido.size
        const comParecer = grupos.comParecer.size
        const total = cumprido + comParecer
        
        return {
          executante,
          cumprido,
          comParecer,
          total,
        }
      })
      .sort((a, b) => b.total - a.total) // Ordenar do maior para o menor

    return NextResponse.json({
      dados,
      total: dados.reduce((sum, item) => sum + item.total, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados de produção por executante:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar dados de produção por executante',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
