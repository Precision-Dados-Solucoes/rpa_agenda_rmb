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
      console.log('[DEBUG permissoes] Sem token de autenticação')
      return null
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)

    if (!decoded) {
      console.log('[DEBUG permissoes] Token inválido ou expirado')
      return null
    }

    console.log('[DEBUG permissoes] Token decodificado:', { id: decoded.id, email: decoded.email, role: decoded.role })

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
      console.log('[DEBUG permissoes] Usuário não encontrado no banco')
      return null
    }

    const permissoes = {
      role: usuario.role || 'usuario',
      paginas_autorizadas: usuario.paginas_autorizadas
        ? JSON.parse(usuario.paginas_autorizadas)
        : [],
      executantes_autorizados: usuario.executantes_autorizados
        ? JSON.parse(usuario.executantes_autorizados)
        : [],
    }

    console.log('[DEBUG permissoes] Permissões obtidas:', {
      role: permissoes.role,
      paginas_count: permissoes.paginas_autorizadas.length,
      executantes_count: permissoes.executantes_autorizados.length,
      executantes: permissoes.executantes_autorizados,
    })

    return permissoes
  } catch (error) {
    console.error('[DEBUG permissoes] Erro ao obter permissões do usuário:', error)
    return null
  }
}
