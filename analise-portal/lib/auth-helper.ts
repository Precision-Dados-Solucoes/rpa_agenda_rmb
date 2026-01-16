import { NextRequest } from 'next/server'
import { prisma } from './prisma'
import { verifyToken } from './auth'
import { PermissoesUsuario } from './permissoes-helper'

/**
 * Obtém as permissões do usuário a partir do token de autenticação
 */
export async function obterPermissoesUsuario(request: NextRequest): Promise<PermissoesUsuario | null> {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return null
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)

    if (!decoded) {
      return null
    }

    // Buscar usuário com permissões
    const usuario = await prisma.usuario.findUnique({
      where: { id: decoded.id },
      select: {
        role: true,
        paginas_autorizadas: true,
        executantes_autorizados: true,
      },
    })

    if (!usuario) {
      return null
    }

    return {
      role: usuario.role || 'usuario',
      paginas_autorizadas: usuario.paginas_autorizadas
        ? JSON.parse(usuario.paginas_autorizadas)
        : [],
      executantes_autorizados: usuario.executantes_autorizados
        ? JSON.parse(usuario.executantes_autorizados)
        : [],
    }
  } catch (error) {
    console.error('Erro ao obter permissões do usuário:', error)
    return null
  }
}
