/**
 * Função auxiliar para construir query SQL com COUNT DISTINCT
 */
export function construirQueryCountDistinct(
  coluna: string,
  where: any,
  tabela: string = 'agenda_base'
): { query: string; params: any[] } {
  const whereConditions: string[] = []
  const params: any[] = []
  let paramIndex = 0

  if (where.executante) {
    whereConditions.push(`executante = ?`)
    params.push(where.executante)
  }
  if (where.status) {
    whereConditions.push(`status = ?`)
    params.push(where.status)
  }
  if (where.etiqueta) {
    whereConditions.push(`etiqueta = ?`)
    params.push(where.etiqueta)
  }
  if (where.subtipo) {
    whereConditions.push(`subtipo = ?`)
    params.push(where.subtipo)
  }
  if (where.pasta_proc) {
    whereConditions.push(`pasta_proc = ?`)
    params.push(where.pasta_proc)
  }
  if (where.inicio_data) {
    if (where.inicio_data.gte) {
      whereConditions.push(`inicio_data >= ?`)
      params.push(where.inicio_data.gte)
    }
    if (where.inicio_data.lte) {
      whereConditions.push(`inicio_data <= ?`)
      params.push(where.inicio_data.lte)
    }
  }
  if (where.conclusao_prevista_data) {
    if (where.conclusao_prevista_data.gte) {
      whereConditions.push(`conclusao_prevista_data >= ?`)
      params.push(where.conclusao_prevista_data.gte)
    }
    if (where.conclusao_prevista_data.lte) {
      whereConditions.push(`conclusao_prevista_data <= ?`)
      params.push(where.conclusao_prevista_data.lte)
    }
  }
  if (where.conclusao_efetiva_data) {
    if (where.conclusao_efetiva_data.gte) {
      whereConditions.push(`conclusao_efetiva_data >= ?`)
      params.push(where.conclusao_efetiva_data.gte)
    }
    if (where.conclusao_efetiva_data.lte) {
      whereConditions.push(`conclusao_efetiva_data <= ?`)
      params.push(where.conclusao_efetiva_data.lte)
    }
  }
  if (where.prazo_fatal_data) {
    if (where.prazo_fatal_data.gte) {
      whereConditions.push(`prazo_fatal_data >= ?`)
      params.push(where.prazo_fatal_data.gte)
    }
    if (where.prazo_fatal_data.lte) {
      whereConditions.push(`prazo_fatal_data <= ?`)
      params.push(where.prazo_fatal_data.lte)
    }
  }

  whereConditions.push(`${coluna} IS NOT NULL`)

  const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : ''

  const query = `
    SELECT 
      ${coluna} as categoria,
      COUNT(DISTINCT id_legalone) as quantidade
    FROM ${tabela}
    ${whereClause}
    GROUP BY ${coluna}
    ORDER BY quantidade DESC
  `

  return { query, params }
}
