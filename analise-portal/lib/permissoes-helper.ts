/**
 * Helper para verificar permissões de usuários baseado em marcações
 */

export interface PermissoesUsuario {
  paginas_autorizadas: string[]
  executantes_autorizados: string[]
  role: string
}

/**
 * Verifica se o usuário tem acesso a uma página específica
 */
export function temAcessoPagina(
  permissoes: PermissoesUsuario | null,
  pagina: 'dashboard_agenda' | 'dashboard_indicadores' | 'gerenciamento_usuarios'
): boolean {
  if (!permissoes) return false

  // Administradores têm acesso total
  if (permissoes.role === 'administrador') {
    return true
  }

  return permissoes.paginas_autorizadas?.includes(pagina) || false
}

/**
 * Verifica se o usuário tem acesso a um executante específico
 */
export function temAcessoExecutante(
  permissoes: PermissoesUsuario | null,
  executante: string | null
): boolean {
  if (!permissoes || !executante) return false

  // Administradores têm acesso a todos os executantes
  if (permissoes.role === 'administrador') {
    return true
  }

  // Array vazio significa acesso a todos
  if (
    !permissoes.executantes_autorizados ||
    permissoes.executantes_autorizados.length === 0
  ) {
    return true
  }

  return permissoes.executantes_autorizados.includes(executante)
}

/**
 * Filtra dados baseado nas permissões de executante do usuário
 */
export function aplicarFiltroExecutante<T extends { executante: string | null }>(
  dados: T[],
  permissoes: PermissoesUsuario | null
): T[] {
  if (!permissoes) return []

  // Administradores veem tudo
  if (permissoes.role === 'administrador') {
    return dados
  }

  // Array vazio significa acesso a todos
  if (
    !permissoes.executantes_autorizados ||
    permissoes.executantes_autorizados.length === 0
  ) {
    return dados
  }

  // Filtrar apenas executantes autorizados
  return dados.filter((item) => {
    if (!item.executante) return false
    return permissoes.executantes_autorizados.includes(item.executante)
  })
}

/**
 * Constrói filtro WHERE para Prisma baseado nas permissões de executante
 */
export function construirWherePermissoes(
  permissoes: PermissoesUsuario | null,
  whereBase: any = {}
): any {
  console.log('[DEBUG construirWherePermissoes] Iniciando:', {
    temPermissoes: !!permissoes,
    role: permissoes?.role,
    executantes_count: permissoes?.executantes_autorizados?.length || 0,
    executantes: permissoes?.executantes_autorizados,
    whereBase_executante: whereBase.executante,
  })

  // Se não houver permissões (sem token), permitir acesso total (compatibilidade)
  if (!permissoes) {
    console.log('[DEBUG construirWherePermissoes] Sem permissões, retornando whereBase sem filtro')
    return whereBase
  }

  // Administradores veem tudo
  if (permissoes.role === 'administrador') {
    console.log('[DEBUG construirWherePermissoes] Administrador, retornando whereBase sem filtro')
    return whereBase
  }

  // Array vazio significa acesso a todos
  if (
    !permissoes.executantes_autorizados ||
    permissoes.executantes_autorizados.length === 0
  ) {
    console.log('[DEBUG construirWherePermissoes] Array vazio de executantes, retornando whereBase sem filtro')
    return whereBase
  }

  // Adicionar filtro de executantes
  // Se já houver um filtro de executante específico, fazer a intersecção
  if (whereBase.executante) {
    // Se o executante filtrado não está na lista de autorizados, retornar vazio
    if (typeof whereBase.executante === 'string') {
      if (!permissoes.executantes_autorizados.includes(whereBase.executante)) {
        console.log('[DEBUG construirWherePermissoes] Executante filtrado não autorizado, retornando vazio')
        return { id_legalone: -1 } // Retornar vazio se o executante filtrado não está autorizado
      }
      // Se está autorizado, manter o filtro específico
      console.log('[DEBUG construirWherePermissoes] Executante filtrado autorizado, mantendo filtro específico')
      return whereBase
    }
  }
  
  // Se não houver filtro específico, aplicar filtro de lista de autorizados
  const whereComFiltro = {
    ...whereBase,
    executante: {
      in: permissoes.executantes_autorizados,
    },
  }
  
  console.log('[DEBUG construirWherePermissoes] Aplicando filtro de executantes autorizados:', {
    executantes_in: permissoes.executantes_autorizados,
    where_final: JSON.stringify(whereComFiltro),
  })
  
  return whereComFiltro
}
