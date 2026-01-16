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
  if (!permissoes) {
    return { id_legalone: -1 } // Retornar vazio se não houver permissões
  }

  // Administradores veem tudo
  if (permissoes.role === 'administrador') {
    return whereBase
  }

  // Array vazio significa acesso a todos
  if (
    !permissoes.executantes_autorizados ||
    permissoes.executantes_autorizados.length === 0
  ) {
    return whereBase
  }

  // Adicionar filtro de executantes
  return {
    ...whereBase,
    executante: {
      in: permissoes.executantes_autorizados,
    },
  }
}
