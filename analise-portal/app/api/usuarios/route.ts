import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import bcrypt from 'bcryptjs'
import { verifyToken } from '@/lib/auth'
// import { enviarEmailBoasVindas } from '@/lib/email' // Desabilitado temporariamente

/**
 * GET /api/usuarios
 * Lista todos os usuários (apenas para administradores)
 */
export async function GET(request: NextRequest) {
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
    const usuario = await prisma.usuario.findUnique({
      where: { id: decoded.id },
      select: { role: true },
    })

    if (!usuario || (usuario.role !== 'administrador' && usuario.role !== 'gerente')) {
      return NextResponse.json({ error: 'Acesso negado' }, { status: 403 })
    }

    // Buscar todos os usuários
    const usuarios = await prisma.usuario.findMany({
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
      orderBy: {
        created_at: 'desc',
      },
    })

    // Parsear JSON strings para arrays
    const usuariosFormatados = usuarios.map((usuario) => ({
      ...usuario,
      paginas_autorizadas: usuario.paginas_autorizadas
        ? JSON.parse(usuario.paginas_autorizadas)
        : [],
      executantes_autorizados: usuario.executantes_autorizados
        ? JSON.parse(usuario.executantes_autorizados)
        : [],
    }))

    return NextResponse.json({ usuarios: usuariosFormatados })
  } catch (error) {
    console.error('Erro ao listar usuários:', error)
    return NextResponse.json(
      {
        error: 'Erro ao listar usuários',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/usuarios
 * Cria um novo usuário (apenas para administradores)
 */
export async function POST(request: NextRequest) {
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
    const usuario = await prisma.usuario.findUnique({
      where: { id: decoded.id },
      select: { role: true },
    })

    if (!usuario || usuario.role !== 'administrador') {
      return NextResponse.json({ error: 'Apenas administradores podem criar usuários' }, { status: 403 })
    }

    const body = await request.json()
    const { email, senha, nome, role, paginas, executantes } = body

    // Validações
    if (!email || !senha || !nome) {
      return NextResponse.json(
        { error: 'Email, senha e nome são obrigatórios' },
        { status: 400 }
      )
    }

    // Validar páginas (se não for administrador)
    if (role !== 'administrador') {
      if (!paginas || !Array.isArray(paginas) || paginas.length === 0) {
        return NextResponse.json(
          { error: 'Selecione ao menos uma página autorizada' },
          { status: 400 }
        )
      }

      if (!executantes || !Array.isArray(executantes) || executantes.length === 0) {
        return NextResponse.json(
          { error: 'Selecione ao menos um executante autorizado' },
          { status: 400 }
        )
      }
    }

    // Verificar se o email já existe
    const usuarioExistente = await prisma.usuario.findUnique({
      where: { email },
    })

    if (usuarioExistente) {
      return NextResponse.json(
        { error: 'Email já cadastrado' },
        { status: 400 }
      )
    }

    // Validar role
    const rolesValidos = ['administrador', 'gerente', 'usuario']
    const roleFinal = role && rolesValidos.includes(role) ? role : 'usuario'

    // Para administradores, dar acesso total
    const paginasFinal = roleFinal === 'administrador'
      ? JSON.stringify(['dashboard_agenda', 'dashboard_indicadores', 'gerenciamento_usuarios'])
      : JSON.stringify(paginas || [])

    const executantesFinal = roleFinal === 'administrador'
      ? JSON.stringify([]) // Array vazio significa todos os executantes
      : JSON.stringify(executantes || [])

    // Hash da senha (ANTES de criar o usuário, para poder enviar a senha original por email)
    const senhaHash = await bcrypt.hash(senha, 10)

    // Criar usuário
    const novoUsuario = await prisma.usuario.create({
      data: {
        email,
        senha: senhaHash,
        nome,
        role: roleFinal,
        ativo: true,
        senha_alterada: false,
        paginas_autorizadas: paginasFinal,
        executantes_autorizados: executantesFinal,
      },
      select: {
        id: true,
        email: true,
        nome: true,
        role: true,
        ativo: true,
        senha_alterada: true,
        created_at: true,
        updated_at: true,
      },
    })

    // Enviar email de boas-vindas (DESABILITADO TEMPORARIAMENTE)
    // TODO: Reativar após resolver configuração SMTP/Office 365
    // Não bloquear a criação do usuário se o email falhar
    /*
    try {
      await enviarEmailBoasVindas(email, nome, senha)
    } catch (emailError) {
      console.error('Erro ao enviar email de boas-vindas (usuário criado mesmo assim):', emailError)
      // Continuar mesmo se o email falhar - o usuário já foi criado
    }
    */
    console.log(`📧 Email de boas-vindas desabilitado temporariamente. Usuário criado: ${nome} (${email}) - Senha: ${senha}`)

    return NextResponse.json({ usuario: novoUsuario }, { status: 201 })
  } catch (error) {
    console.error('Erro ao criar usuário:', error)
    return NextResponse.json(
      {
        error: 'Erro ao criar usuário',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
