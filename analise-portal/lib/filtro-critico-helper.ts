/**
 * Função auxiliar para aplicar filtro "Crítico" usando a mesma lógica do semáforo
 * Quando prazoFatalFrom === prazoFatalTo, filtra registros onde diffDays === 0
 */
export function aplicarFiltroCritico<T extends { prazo_fatal_data: Date | string | null }>(
  registros: T[],
  prazoFatalFrom: string | null,
  prazoFatalTo: string | null
): T[] {
  // Verificar se é filtro "Crítico" (from === to)
  const isFiltroCritico = prazoFatalFrom && prazoFatalTo && prazoFatalFrom === prazoFatalTo

  if (!isFiltroCritico) {
    return registros
  }

  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)

  // Filtrar usando a mesma lógica do semáforo (Math.ceil, diffDays === 0)
  return registros.filter((item) => {
    if (!item.prazo_fatal_data) return false

    const prazoFatal = new Date(item.prazo_fatal_data)
    prazoFatal.setHours(0, 0, 0, 0)

    const diffTime = prazoFatal.getTime() - hoje.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    return diffDays === 0 // Apenas registros onde diffDays === 0 (Crítico)
  })
}
