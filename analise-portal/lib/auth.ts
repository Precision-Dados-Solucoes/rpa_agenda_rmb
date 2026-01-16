import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { prisma } from './prisma'

const JWT_SECRET = process.env.JWT_SECRET || 'sua-chave-secreta-jwt-mude-isso'

export interface UserPayload {
  id: string
  email: string
  nome: string
  role: string
}

/**
 * Verifica credenciais de login
 */
export async function verifyCredentials(email: string, senha: string) {
  try {
    // Verificar se o Prisma está configurado
    if (!prisma) {
      throw new Error('Prisma client não está inicializado')
    }

    const usuario = await prisma.usuario.findUnique({
      where: { email },
      select: {
        id: true,
        email: true,
        nome: true,
        role: true,
        senha: true,
        ativo: true,
        senha_alterada: true,
        paginas_autorizadas: true,
        executantes_autorizados: true,
      },
    })

    if (!usuario || !usuario.ativo) {
      return null
    }

    const senhaValida = await bcrypt.compare(senha, usuario.senha)

    if (!senhaValida) {
      return null
    }

    return {
      id: usuario.id,
      email: usuario.email,
      nome: usuario.nome,
      role: usuario.role,
      senha_alterada: usuario.senha_alterada ?? false,
      paginas_autorizadas: usuario.paginas_autorizadas
        ? JSON.parse(usuario.paginas_autorizadas)
        : [],
      executantes_autorizados: usuario.executantes_autorizados
        ? JSON.parse(usuario.executantes_autorizados)
        : [],
    }
  } catch (error) {
    console.error('Erro em verifyCredentials:', error)
    if (error instanceof Error) {
      console.error('Tipo do erro:', error.constructor.name)
      console.error('Mensagem:', error.message)
    }
    throw error
  }
}

/**
 * Gera token JWT
 */
export function generateToken(payload: UserPayload): string {
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: '24h',
  })
}

/**
 * Verifica e decodifica token JWT
 */
export function verifyToken(token: string): UserPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET) as UserPayload
  } catch {
    return null
  }
}

/**
 * Cria sessão no banco de dados
 */
export async function createSession(
  usuarioId: string,
  token: string,
  ipAddress?: string,
  userAgent?: string
) {
  const expiresAt = new Date()
  expiresAt.setHours(expiresAt.getHours() + 24) // 24 horas

  return await prisma.sessao.create({
    data: {
      usuario_id: usuarioId,
      token,
      expires_at: expiresAt,
      ip_address: ipAddress,
      user_agent: userAgent,
    },
  })
}

/**
 * Remove sessão (logout)
 */
export async function removeSession(token: string) {
  return await prisma.sessao.deleteMany({
    where: { token },
  })
}

/**
 * Registra log de acesso
 */
export async function logAccess(
  usuarioId: string | null,
  acao: string,
  endpoint?: string,
  metodo?: string,
  ipAddress?: string,
  userAgent?: string,
  statusCode?: number,
  detalhes?: string
) {
  return await prisma.logsAcessos.create({
    data: {
      usuario_id: usuarioId,
      acao,
      endpoint,
      metodo,
      ip_address: ipAddress,
      user_agent: userAgent,
      status_code: statusCode,
      detalhes,
    },
  })
}

/**
 * Atualiza senha do usuário
 */
export async function updatePassword(usuarioId: string, novaSenha: string) {
  const senhaHash = await bcrypt.hash(novaSenha, 10)

  return await prisma.usuario.update({
    where: { id: usuarioId },
    data: {
      senha: senhaHash,
      senha_alterada: true,
    },
  })
}
