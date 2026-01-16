import { NextRequest, NextResponse } from 'next/server'
import { verifyToken, verifyCredentials, updatePassword, generateToken, logAccess } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    // Verificar autenticação
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Não autorizado' },
        { status: 401 }
      )
    }

    const token = authHeader.substring(7)
    const payload = verifyToken(token)

    if (!payload) {
      return NextResponse.json(
        { error: 'Token inválido ou expirado' },
        { status: 401 }
      )
    }

    const { senhaAtual, novaSenha } = await request.json()

    if (!senhaAtual || !novaSenha) {
      return NextResponse.json(
        { error: 'Senha atual e nova senha são obrigatórias' },
        { status: 400 }
      )
    }

    if (novaSenha.length < 6) {
      return NextResponse.json(
        { error: 'A nova senha deve ter pelo menos 6 caracteres' },
        { status: 400 }
      )
    }

    // Verificar senha atual
    const usuario = await verifyCredentials(payload.email, senhaAtual)

    if (!usuario) {
      await logAccess(
        payload.id,
        'trocar_senha_falhou',
        '/api/auth/trocar-senha',
        'POST',
        request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || undefined,
        request.headers.get('user-agent') || undefined,
        401,
        'Senha atual incorreta'
      )

      return NextResponse.json(
        { error: 'Senha atual incorreta' },
        { status: 401 }
      )
    }

    // Atualizar senha
    await updatePassword(payload.id, novaSenha)

    // Gerar novo token
    const newToken = generateToken({
      id: payload.id,
      email: payload.email,
      nome: payload.nome,
      role: payload.role,
    })

    // Registrar troca de senha
    await logAccess(
      payload.id,
      'senha_alterada',
      '/api/auth/trocar-senha',
      'POST',
      request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || undefined,
      request.headers.get('user-agent') || undefined,
      200
    )

    return NextResponse.json({
      message: 'Senha alterada com sucesso',
      token: newToken,
    })
  } catch (error) {
    console.error('Erro ao trocar senha:', error)
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    )
  }
}
