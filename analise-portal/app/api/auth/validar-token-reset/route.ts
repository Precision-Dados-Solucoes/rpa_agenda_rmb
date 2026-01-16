import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

/**
 * GET /api/auth/validar-token-reset
 * Valida se o token de reset é válido
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const token = searchParams.get('token')

    if (!token) {
      return NextResponse.json(
        { valido: false, error: 'Token não fornecido' },
        { status: 400 }
      )
    }

    // Buscar usuário com este token
    const usuario = await prisma.usuario.findFirst({
      where: {
        reset_token: token,
        reset_token_expires: {
          gt: new Date(), // Token ainda não expirou
        },
      },
    })

    if (!usuario) {
      return NextResponse.json({
        valido: false,
        error: 'Token inválido ou expirado',
      })
    }

    return NextResponse.json({
      valido: true,
      email: usuario.email,
    })
  } catch (error) {
    console.error('Erro ao validar token:', error)
    return NextResponse.json(
      {
        valido: false,
        error: 'Erro ao validar token',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
