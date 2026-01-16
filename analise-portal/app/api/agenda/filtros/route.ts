import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

/**
 * GET /api/agenda/filtros
 * Retorna valores únicos para popular os dropdowns de filtros
 */
export async function GET(request: NextRequest) {
  try {
    // Buscar valores únicos de cada coluna de filtro
    const [executantes, status, complexidades, tipos, pastas] = await Promise.all([
      // Executantes (coluna executante)
      prisma.$queryRawUnsafe<Array<{ executante: string }>>(
        `SELECT DISTINCT executante 
         FROM agenda_base 
         WHERE executante IS NOT NULL AND executante != ''
         ORDER BY executante`
      ),
      
      // Status (coluna status)
      prisma.$queryRawUnsafe<Array<{ status: string }>>(
        `SELECT DISTINCT status 
         FROM agenda_base 
         WHERE status IS NOT NULL AND status != ''
         ORDER BY status`
      ),
      
      // Complexidade (coluna etiqueta)
      prisma.$queryRawUnsafe<Array<{ etiqueta: string }>>(
        `SELECT DISTINCT etiqueta 
         FROM agenda_base 
         WHERE etiqueta IS NOT NULL AND etiqueta != ''
         ORDER BY etiqueta`
      ),
      
      // Tipo (coluna subtipo)
      prisma.$queryRawUnsafe<Array<{ subtipo: string }>>(
        `SELECT DISTINCT subtipo 
         FROM agenda_base 
         WHERE subtipo IS NOT NULL AND subtipo != ''
         ORDER BY subtipo`
      ),
      
      // Pasta (coluna pasta_proc)
      prisma.$queryRawUnsafe<Array<{ pasta_proc: string }>>(
        `SELECT DISTINCT pasta_proc 
         FROM agenda_base 
         WHERE pasta_proc IS NOT NULL AND pasta_proc != ''
         ORDER BY pasta_proc`
      ),
    ])

    // Buscar ranges de datas
    const [dataInicioRange, conclusaoPrevistaRange, conclusaoEfetivaRange, prazoFatalRange] = await Promise.all([
      prisma.$queryRawUnsafe<Array<{ min: Date; max: Date }>>(
        `SELECT 
          MIN(inicio_data) as min,
          MAX(inicio_data) as max
         FROM agenda_base
         WHERE inicio_data IS NOT NULL`
      ),
      prisma.$queryRawUnsafe<Array<{ min: Date; max: Date }>>(
        `SELECT 
          MIN(conclusao_prevista_data) as min,
          MAX(conclusao_prevista_data) as max
         FROM agenda_base
         WHERE conclusao_prevista_data IS NOT NULL`
      ),
      prisma.$queryRawUnsafe<Array<{ min: Date; max: Date }>>(
        `SELECT 
          MIN(conclusao_efetiva_data) as min,
          MAX(conclusao_efetiva_data) as max
         FROM agenda_base
         WHERE conclusao_efetiva_data IS NOT NULL`
      ),
      prisma.$queryRawUnsafe<Array<{ min: Date; max: Date }>>(
        `SELECT 
          MIN(prazo_fatal_data) as min,
          MAX(prazo_fatal_data) as max
         FROM agenda_base
         WHERE prazo_fatal_data IS NOT NULL`
      ),
    ])

    return NextResponse.json({
      executantes: executantes.map(r => r.executante).filter(Boolean),
      status: status.map(r => r.status).filter(Boolean),
      complexidades: complexidades.map(r => r.etiqueta).filter(Boolean),
      tipos: tipos.map(r => r.subtipo).filter(Boolean),
      pastas: pastas.map(r => r.pasta_proc).filter(Boolean),
      ranges: {
        dataInicio: {
          min: dataInicioRange[0]?.min ? new Date(dataInicioRange[0].min).toISOString() : null,
          max: dataInicioRange[0]?.max ? new Date(dataInicioRange[0].max).toISOString() : null,
        },
        conclusaoPrevista: {
          min: conclusaoPrevistaRange[0]?.min ? new Date(conclusaoPrevistaRange[0].min).toISOString() : null,
          max: conclusaoPrevistaRange[0]?.max ? new Date(conclusaoPrevistaRange[0].max).toISOString() : null,
        },
        conclusaoEfetiva: {
          min: conclusaoEfetivaRange[0]?.min ? new Date(conclusaoEfetivaRange[0].min).toISOString() : null,
          max: conclusaoEfetivaRange[0]?.max ? new Date(conclusaoEfetivaRange[0].max).toISOString() : null,
        },
        prazoFatal: {
          min: prazoFatalRange[0]?.min ? new Date(prazoFatalRange[0].min).toISOString() : null,
          max: prazoFatalRange[0]?.max ? new Date(prazoFatalRange[0].max).toISOString() : null,
        },
      },
    })
  } catch (error) {
    console.error('Erro ao buscar filtros:', error)
    return NextResponse.json(
      { error: 'Erro ao buscar filtros' },
      { status: 500 }
    )
  }
}
