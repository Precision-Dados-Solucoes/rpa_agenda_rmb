import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { construirWhere } from '@/lib/filtros-helper'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { construirWherePermissoes } from '@/lib/permissoes-helper'

/**
 * GET /api/indicadores/complexidade-executante
 * Retorna contagem de id_legalone únicos por executante e complexidade
 * Apenas para status "Cumprido" ou "Cumprido com parecer"
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

    // Buscar registros com status "Cumprido" ou "Cumprido com parecer"
    const registros = await prisma.agendaBase.findMany({
      where: {
        ...whereBaseComPermissoes,
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
        etiqueta: true,
      },
    })

    // Agrupar por executante e etiqueta, contando id_legalone únicos
    // Excluir registros sem etiqueta (Em branco)
    const agrupado = new Map<
      string,
      {
        alta: Set<string>
        media: Set<string>
        baixa: Set<string>
      }
    >()

    registros.forEach((registro) => {
      const executante = registro.executante || '(Em branco)'
      const id = registro.id_legalone.toString()
      const etiqueta = registro.etiqueta

      // Ignorar registros sem etiqueta
      if (!etiqueta || etiqueta.trim() === '') {
        return
      }

      if (!agrupado.has(executante)) {
        agrupado.set(executante, {
          alta: new Set(),
          media: new Set(),
          baixa: new Set(),
        })
      }

      const grupo = agrupado.get(executante)!

      // Classificar por etiqueta
      if (etiqueta.toLowerCase().includes('alta')) {
        grupo.alta.add(id)
      } else if (etiqueta.toLowerCase().includes('média') || etiqueta.toLowerCase().includes('media')) {
        grupo.media.add(id)
      } else if (etiqueta.toLowerCase().includes('baixa')) {
        grupo.baixa.add(id)
      }
      // Se não se encaixar em nenhuma categoria conhecida, ignorar
    })

    // Converter para array e calcular totais e percentuais
    const dados = Array.from(agrupado.entries())
      .map(([executante, grupos]) => {
        const alta = grupos.alta.size
        const media = grupos.media.size
        const baixa = grupos.baixa.size
        const total = alta + media + baixa

        return {
          executante,
          alta,
          media,
          baixa,
          total,
          altaPercent: total > 0 ? (alta / total) * 100 : 0,
          mediaPercent: total > 0 ? (media / total) * 100 : 0,
          baixaPercent: total > 0 ? (baixa / total) * 100 : 0,
        }
      })
      .filter((item) => item.total > 0) // Filtrar executantes sem dados
      .sort((a, b) => b.total - a.total) // Ordenar do maior para o menor

    return NextResponse.json({
      dados,
      total: dados.reduce((sum, item) => sum + item.total, 0),
    })
  } catch (error) {
    console.error('Erro ao buscar dados de complexidade por executante:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar dados de complexidade por executante',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
