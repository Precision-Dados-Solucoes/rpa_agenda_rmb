import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

/**
 * GET /api/usuarios/executantes
 * Retorna lista de executantes únicos para seleção
 */
export async function GET(request: NextRequest) {
  try {
    const executantes = await prisma.$queryRawUnsafe<Array<{ executante: string }>>(
      `SELECT DISTINCT executante 
       FROM agenda_base 
       WHERE executante IS NOT NULL AND executante != ''
       ORDER BY executante`
    )

    return NextResponse.json({
      executantes: executantes.map((e) => e.executante),
    })
  } catch (error) {
    console.error('Erro ao buscar executantes:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar executantes',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
