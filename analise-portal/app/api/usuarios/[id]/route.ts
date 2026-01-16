import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import bcrypt from 'bcryptjs'
import { verifyToken } from '@/lib/auth'

/**
 * GET /api/usuarios/[id]
 * Retorna detalhes de um usuário específico
 */
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const params = await context.params
  try {
    // Verificar autenticação
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Não autorizado' }, { status: 401 })
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)

    if (!decoded) {
      return NextResponse.json({ error: 'Token inválido' }, { status: 401 })
    }

    // Verificar se é administrador ou gerente
    const usuarioLogado = await prisma.usuario.findUnique({
      where: { id: decoded.id },
      select: { role: true },
    })

    if (!usuarioLogado || (usuarioLogado.role !== 'administrador' && usuarioLogado.role !== 'gerente')) {
      return NextResponse.json({ error: 'Acesso negado' }, { status: 403 })
    }

    const usuario = await prisma.usuario.findUnique({
      where: { id: params.id },
      select: {
        id: true,
        email: true,
        nome: true,
        role: true,
        ativo: true,
        senha_alterada: true,
        paginas_autorizadas: true,
        executantes_autorizados: true,
        created_at: true,
        updated_at: true,
      },
    })

    if (!usuario) {
      return NextResponse.json({ error: 'Usuário não encontrado' }, { status: 404 })
    }

    // Parsear JSON strings para arrays
    const usuarioFormatado = {
      ...usuario,
      paginas_autorizadas: usuario.paginas_autorizadas
        ? JSON.parse(usuario.paginas_autorizadas)
        : [],
      executantes_autorizados: usuario.executantes_autorizados
        ? JSON.parse(usuario.executantes_autorizados)
        : [],
    }

    return NextResponse.json({ usuario: usuarioFormatado })
  } catch (error) {
    console.error('Erro ao buscar usuário:', error)
    return NextResponse.json(
      {
        error: 'Erro ao buscar usuário',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}

/**
 * PUT /api/usuarios/[id]
 * Atualiza um usuário existente
 */
export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const params = await context.params
  try {
    // Verificar autenticação
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Não autorizado' }, { status: 401 })
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)

    if (!decoded) {
      return NextResponse.json({ error: 'Token inválido' }, { status: 401 })
    }

    // Verificar se é administrador
    const usuarioLogado = await prisma.usuario.findUnique({
      where: { id: decoded.id },
      select: { role: true },
    })

    if (!usuarioLogado || usuarioLogado.role !== 'administrador') {
      return NextResponse.json(
        { error: 'Apenas administradores podem editar usuários' },
        { status: 403 }
      )
    }

    const body = await request.json()
    const { nome, role, ativo, paginas, executantes, senha } = body

    // Verificar se o usuário existe
    const usuarioExistente = await prisma.usuario.findUnique({
      where: { id: params.id },
    })

    if (!usuarioExistente) {
      return NextResponse.json({ error: 'Usuário não encontrado' }, { status: 404 })
    }

    // Validar role
    const rolesValidos = ['administrador', 'gerente', 'usuario']
    const roleFinal = role && rolesValidos.includes(role) ? role : usuarioExistente.role

    // Preparar dados de atualização
    const dadosAtualizacao: any = {}

    if (nome !== undefined) dadosAtualizacao.nome = nome
    if (role !== undefined) dadosAtualizacao.role = roleFinal
    if (ativo !== undefined) dadosAtualizacao.ativo = ativo

    // Atualizar senha se fornecida
    if (senha && senha.length >= 6) {
      dadosAtualizacao.senha = await bcrypt.hash(senha, 10)
      dadosAtualizacao.senha_alterada = false // Resetar flag ao alterar senha
    }

    // Atualizar permissões (se não for administrador)
    if (roleFinal !== 'administrador') {
      if (paginas !== undefined) {
        if (!Array.isArray(paginas) || paginas.length === 0) {
          return NextResponse.json(
            { error: 'Selecione ao menos uma página autorizada' },
            { status: 400 }
          )
        }
        dadosAtualizacao.paginas_autorizadas = JSON.stringify(paginas)
      }

      if (executantes !== undefined) {
        if (!Array.isArray(executantes) || executantes.length === 0) {
          return NextResponse.json(
            { error: 'Selecione ao menos um executante autorizado' },
            { status: 400 }
          )
        }
        dadosAtualizacao.executantes_autorizados = JSON.stringify(executantes)
      }
    } else {
      // Administradores têm acesso total
      dadosAtualizacao.paginas_autorizadas = JSON.stringify([
        'dashboard_agenda',
        'dashboard_indicadores',
        'gerenciamento_usuarios',
      ])
      dadosAtualizacao.executantes_autorizados = JSON.stringify([])
    }

    // Atualizar usuário
    const usuarioAtualizado = await prisma.usuario.update({
      where: { id: params.id },
      data: dadosAtualizacao,
      select: {
        id: true,
        email: true,
        nome: true,
        role: true,
        ativo: true,
        senha_alterada: true,
        paginas_autorizadas: true,
        executantes_autorizados: true,
        created_at: true,
        updated_at: true,
      },
    })

    // Parsear JSON strings para arrays
    const usuarioFormatado = {
      ...usuarioAtualizado,
      paginas_autorizadas: usuarioAtualizado.paginas_autorizadas
        ? JSON.parse(usuarioAtualizado.paginas_autorizadas)
        : [],
      executantes_autorizados: usuarioAtualizado.executantes_autorizados
        ? JSON.parse(usuarioAtualizado.executantes_autorizados)
        : [],
    }

    return NextResponse.json({ usuario: usuarioFormatado })
  } catch (error) {
    console.error('Erro ao atualizar usuário:', error)
    return NextResponse.json(
      {
        error: 'Erro ao atualizar usuário',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
