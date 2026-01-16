import { NextRequest, NextResponse } from 'next/server'
import { verifyCredentials, generateToken, createSession, logAccess } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    const { email, senha } = await request.json()

    if (!email || !senha) {
      return NextResponse.json(
        { error: 'Email e senha são obrigatórios' },
        { status: 400 }
      )
    }

    // Verificar credenciais
    const usuario = await verifyCredentials(email, senha)

    if (!usuario) {
      // Registrar tentativa de login falhada
      await logAccess(
        null,
        'login_falhou',
        '/api/auth/login',
        'POST',
        request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || undefined,
        request.headers.get('user-agent') || undefined,
        401,
        JSON.stringify({ email })
      )

      return NextResponse.json(
        { error: 'Email ou senha incorretos' },
        { status: 401 }
      )
    }

    // Gerar token
    const token = generateToken({
      id: usuario.id,
      email: usuario.email,
      nome: usuario.nome,
      role: usuario.role,
    })

    // Criar sessão
    await createSession(
      usuario.id,
      token,
      request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || undefined,
      request.headers.get('user-agent') || undefined
    )

    // Registrar login bem-sucedido
    await logAccess(
      usuario.id,
      'login',
      '/api/auth/login',
      'POST',
      request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || undefined,
      request.headers.get('user-agent') || undefined,
      200
    )

    return NextResponse.json({
      token,
      user: {
        id: usuario.id,
        email: usuario.email,
        nome: usuario.nome,
        role: usuario.role,
      },
      primeiroAcesso: !usuario.senha_alterada,
    })
  } catch (error) {
    console.error('='.repeat(50))
    console.error('ERRO NO LOGIN - Detalhes completos:')
    console.error('='.repeat(50))
    console.error('Mensagem:', error instanceof Error ? error.message : String(error))
    console.error('Stack trace:', error instanceof Error ? error.stack : 'No stack trace')
    
    // Verificar se é erro de conexão com banco
    if (error instanceof Error) {
      if (error.message.includes('DATABASE_URL') || error.message.includes('Environment variable')) {
        console.error('⚠️ ERRO: Variável DATABASE_URL não encontrada!')
        console.error('⚠️ Verifique se o arquivo .env.local existe e se o servidor foi reiniciado.')
      }
      if (error.message.includes("Can't reach database")) {
        console.error('⚠️ ERRO: Não foi possível conectar ao banco de dados!')
        console.error('⚠️ Verifique a string de conexão e o firewall do Azure.')
      }
    }
    
    console.error('='.repeat(50))
    
    return NextResponse.json(
      { 
        error: 'Erro interno do servidor',
        details: process.env.NODE_ENV === 'development' ? (error instanceof Error ? error.message : String(error)) : undefined
      },
      { status: 500 }
    )
  }
}
