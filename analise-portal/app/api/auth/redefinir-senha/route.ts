import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import bcrypt from 'bcryptjs'

/**
 * POST /api/auth/redefinir-senha
 * Redefine a senha usando o token de reset
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { token, senha } = body

    if (!token || !senha) {
      return NextResponse.json(
        { error: 'Token e senha são obrigatórios' },
        { status: 400 }
      )
    }

    if (senha.length < 6) {
      return NextResponse.json(
        { error: 'A senha deve ter no mínimo 6 caracteres' },
        { status: 400 }
      )
    }

    // Buscar usuário com este token válido
    const usuario = await prisma.usuario.findFirst({
      where: {
        reset_token: token,
        reset_token_expires: {
          gt: new Date(), // Token ainda não expirou
        },
      },
    })

    if (!usuario) {
      return NextResponse.json(
        { error: 'Token inválido ou expirado' },
        { status: 400 }
      )
    }

    // Hash da nova senha
    const senhaHash = await bcrypt.hash(senha, 10)

    // Atualizar senha e limpar token
    await prisma.usuario.update({
      where: { id: usuario.id },
      data: {
        senha: senhaHash,
        reset_token: null,
        reset_token_expires: null,
        senha_alterada: true, // Marcar que a senha foi alterada
      },
    })

    return NextResponse.json({
      message: 'Senha redefinida com sucesso',
    })
  } catch (error) {
    console.error('Erro ao redefinir senha:', error)
    return NextResponse.json(
      {
        error: 'Erro ao redefinir senha',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
