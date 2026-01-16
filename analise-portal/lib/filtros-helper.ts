/**
 * Função auxiliar para construir objeto where do Prisma baseado nos filtros
 * Aceita URLSearchParams ou objeto Filtros
 */
export function construirWhere(searchParams: URLSearchParams | { [key: string]: string | null }) {
  const where: any = {}

  const getParam = (key: string) => {
    if (searchParams instanceof URLSearchParams) {
      return searchParams.get(key)
    }
    return searchParams[key] || null
  }

  const executante = getParam('executante')
  const status = getParam('status')
  const complexidade = getParam('complexidade')
  const tipo = getParam('tipo')
  const pasta = getParam('pasta')
  const dataInicioFrom = getParam('dataInicioFrom')
  const dataInicioTo = getParam('dataInicioTo')
  const conclusaoPrevistaFrom = getParam('conclusaoPrevistaFrom')
  const conclusaoPrevistaTo = getParam('conclusaoPrevistaTo')
  const conclusaoEfetivaFrom = getParam('conclusaoEfetivaFrom')
  const conclusaoEfetivaTo = getParam('conclusaoEfetivaTo')
  const prazoFatalFrom = getParam('prazoFatalFrom')
  const prazoFatalTo = getParam('prazoFatalTo')

  if (executante && executante !== 'Todos') where.executante = executante
  if (status && status !== 'Todos') where.status = status
  if (complexidade && complexidade !== 'Todos') where.etiqueta = complexidade
  if (tipo && tipo !== 'Todos') where.subtipo = tipo
  if (pasta && pasta !== 'Todos') where.pasta_proc = pasta

  if (dataInicioFrom || dataInicioTo) {
    where.inicio_data = {}
    if (dataInicioFrom) where.inicio_data.gte = new Date(dataInicioFrom)
    if (dataInicioTo) where.inicio_data.lte = new Date(dataInicioTo)
  }

  if (conclusaoPrevistaFrom || conclusaoPrevistaTo) {
    where.conclusao_prevista_data = {}
    if (conclusaoPrevistaFrom) where.conclusao_prevista_data.gte = new Date(conclusaoPrevistaFrom)
    if (conclusaoPrevistaTo) where.conclusao_prevista_data.lte = new Date(conclusaoPrevistaTo)
  }

  if (conclusaoEfetivaFrom || conclusaoEfetivaTo) {
    where.conclusao_efetiva_data = {}
    if (conclusaoEfetivaFrom) where.conclusao_efetiva_data.gte = new Date(conclusaoEfetivaFrom)
    if (conclusaoEfetivaTo) where.conclusao_efetiva_data.lte = new Date(conclusaoEfetivaTo)
  }

  if (prazoFatalFrom || prazoFatalTo) {
    where.prazo_fatal_data = {}
    if (prazoFatalFrom) where.prazo_fatal_data.gte = new Date(prazoFatalFrom)
    if (prazoFatalTo) where.prazo_fatal_data.lte = new Date(prazoFatalTo)
  }

  return where
}
