import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'

/**
 * GET /api/indicadores/producao-executante
 * Retorna contagem de id_legalone únicos por executante
 * Separado por status: "Cumprido" e "Cumprido com parecer"
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Construir where base usando o helper
    const whereBase = construirWhere(searchParams)

    // Buscar registros com status "Cumprido" ou "Cumprido com parecer"
    const registros = await prisma.agendaBase.findMany({
      where: {
        ...whereBase,
        status: {
          in: ['Cumprido', 'Cumprido com parecer'],
        },
        executante: {
          not: null,
        },
      },
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
