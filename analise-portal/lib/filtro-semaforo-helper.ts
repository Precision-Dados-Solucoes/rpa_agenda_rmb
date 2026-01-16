/**
 * Detecta qual categoria do semáforo está sendo filtrada baseado nos parâmetros
 */
export function detectarCategoriaSemaforo(
  prazoFatalFrom: string | null,
  prazoFatalTo: string | null
): string | null {
  if (!prazoFatalFrom && !prazoFatalTo) return null
  
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  
  // Possível perda: from = 2026-01-01 e sem to
  if (prazoFatalFrom === '2026-01-01' && !prazoFatalTo) {
    return 'Possível perda'
  }
  
  // Crítico: from === to (mesmo dia)
  if (prazoFatalFrom && prazoFatalTo && prazoFatalFrom === prazoFatalTo) {
    return 'Crítico'
  }
  
  // Normal: apenas from definido (sem to) e from >= 6 dias a partir de hoje
  if (prazoFatalFrom && !prazoFatalTo) {
    // Verificar se não é "Possível perda" primeiro
    if (prazoFatalFrom !== '2026-01-01') {
      const dataFrom = new Date(prazoFatalFrom + 'T00:00:00')
      const diffFrom = Math.ceil((dataFrom.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24))
      // Se a data from for 6 ou mais dias no futuro, é Normal
      // Aceitar 5 ou 6 devido a possíveis diferenças de timezone
      if (diffFrom >= 5) {
        return 'Normal'
      }
    }
  }
  
  // Atenção, Próximo ou Normal: ambos from e to definidos
  if (prazoFatalFrom && prazoFatalTo) {
    const dataFrom = new Date(prazoFatalFrom)
    dataFrom.setHours(0, 0, 0, 0)
    const dataTo = new Date(prazoFatalTo)
    dataTo.setHours(23, 59, 59, 999)
    
    // Calcular diferença em dias usando Math.ceil (mesma lógica do semáforo)
    // Isso garante que datas no mesmo dia ou próximas sejam calculadas corretamente
    const diffFrom = Math.ceil((dataFrom.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24))
    const diffTo = Math.ceil((dataTo.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24))
    
    // Para detectar a categoria, verificar se o range corresponde
    // Atenção: 1-2 dias, Próximo: 3-5 dias
    // Aceitar ranges próximos devido a possíveis diferenças de timezone
    if ((diffFrom === 1 || diffFrom === 0) && (diffTo === 2 || diffTo === 1 || diffTo === 3)) {
      return 'Atenção'
    } else if ((diffFrom === 3 || diffFrom === 2) && (diffTo === 5 || diffTo === 4 || diffTo === 6)) {
      return 'Próximo'
    } else if (diffFrom >= 6 && diffTo >= 6) {
      return 'Normal'
    }
  }
  
  return null
}

/**
 * Constrói o where query para buscar registros próximos baseado na categoria
 */
export function construirWhereSemaforo(
  where: any,
  categoria: string | null
): any {
  if (!categoria) return where
  
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  
  switch (categoria) {
    case 'Crítico': {
      const ontem = new Date(hoje)
      ontem.setDate(ontem.getDate() - 1)
      const amanha = new Date(hoje)
      amanha.setDate(amanha.getDate() + 1)
      amanha.setHours(23, 59, 59, 999)
      return {
        ...where,
        prazo_fatal_data: {
          not: null,
          gte: ontem,
          lte: amanha,
        },
      }
    }
    case 'Atenção': {
      // Buscar desde ontem até 3 dias no futuro para capturar todos os registros que podem ser Atenção (1-2 dias)
      const hojeMenos1 = new Date(hoje)
      hojeMenos1.setDate(hojeMenos1.getDate() - 1)
      const amanhaMais3 = new Date(hoje)
      amanhaMais3.setDate(amanhaMais3.getDate() + 3)
      amanhaMais3.setHours(23, 59, 59, 999)
      return {
        ...where,
        prazo_fatal_data: {
          not: null,
          gte: hojeMenos1,
          lte: amanhaMais3,
        },
      }
    }
    case 'Próximo': {
      // Buscar desde ontem até 6 dias no futuro para capturar todos os registros que podem ser Próximo (3-5 dias)
      const hojeMenos1 = new Date(hoje)
      hojeMenos1.setDate(hojeMenos1.getDate() - 1)
      const amanhaMais6 = new Date(hoje)
      amanhaMais6.setDate(amanhaMais6.getDate() + 6)
      amanhaMais6.setHours(23, 59, 59, 999)
      return {
        ...where,
        prazo_fatal_data: {
          not: null,
          gte: hojeMenos1,
          lte: amanhaMais6,
        },
      }
    }
    case 'Normal': {
      const amanhaMais5 = new Date(hoje)
      amanhaMais5.setDate(amanhaMais5.getDate() + 5)
      const futuro = new Date(hoje)
      futuro.setDate(futuro.getDate() + 365) // Buscar até 1 ano no futuro
      futuro.setHours(23, 59, 59, 999)
      return {
        ...where,
        prazo_fatal_data: {
          not: null,
          gte: amanhaMais5,
          lte: futuro,
        },
      }
    }
    case 'Possível perda': {
      const dataLimite = new Date('2026-01-01')
      dataLimite.setHours(0, 0, 0, 0)
      const amanha = new Date(hoje)
      amanha.setDate(amanha.getDate() + 1)
      amanha.setHours(23, 59, 59, 999)
      return {
        ...where,
        prazo_fatal_data: {
          not: null,
          gte: dataLimite,
          lte: amanha,
        },
      }
    }
    default:
      return where
  }
}

/**
 * Função auxiliar para aplicar filtro do semáforo usando a mesma lógica de cálculo
 * Aplica a mesma lógica do semáforo-fatal para cada categoria
 */
export function aplicarFiltroSemaforo<T extends { prazo_fatal_data: Date | string | null }>(
  registros: T[],
  categoria: string
): T[] {
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  
  const dataLimitePossivelPerda = new Date('2026-01-01')
  dataLimitePossivelPerda.setHours(0, 0, 0, 0)

  let contador = 0
  const resultado = registros.filter((item) => {
    if (!item.prazo_fatal_data) return false

    const prazoFatal = new Date(item.prazo_fatal_data)
    prazoFatal.setHours(0, 0, 0, 0)

    // Calcular diferença em dias (mesma lógica do semáforo)
    const diffTime = prazoFatal.getTime() - hoje.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    // Classificar usando a mesma lógica do semáforo
    let match = false
    switch (categoria) {
      case 'Possível perda':
        match = diffDays < 0 && prazoFatal >= dataLimitePossivelPerda
        break
      case 'Crítico':
        match = diffDays === 0
        break
      case 'Atenção':
        match = diffDays === 1 || diffDays === 2
        break
      case 'Próximo':
        match = diffDays >= 3 && diffDays <= 5
        break
      case 'Normal':
        match = diffDays >= 6
        break
      default:
        match = false
    }
    
    if (match) contador++
    return match
  })
  
  console.log('[DEBUG aplicarFiltroSemaforo]', {
    categoria,
    totalRegistros: registros.length,
    registrosFiltrados: resultado.length,
    contador,
  })

  return resultado
}
