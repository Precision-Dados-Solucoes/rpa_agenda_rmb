import { NextRequest, NextResponse } from 'next/server'
import { obterPermissoesUsuario } from '@/lib/auth-helper'
import { verifyToken } from '@/lib/auth'

/**
 * GET /api/debug/permissoes
 * Endpoint de debug para verificar permissões do usuário
 */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({
        error: 'Sem token',
        temToken: false,
      })
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)

    if (!decoded) {
      return NextResponse.json({
        error: 'Token inválido',
        temToken: true,
        tokenValido: false,
      })
    }

    const permissoes = await obterPermissoesUsuario(request)

    return NextResponse.json({
      tokenValido: true,
      usuario: {
        id: decoded.id,
        email: decoded.email,
        nome: decoded.nome,
        role: decoded.role,
      },
      permissoes,
      localStorage: {
        // Instruções para verificar no frontend
        instrucao: 'Verifique no console do navegador: localStorage.getItem("user")',
      },
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Erro ao verificar permissões',
      details: error instanceof Error ? error.message : String(error),
    }, { status: 500 })
  }
}
