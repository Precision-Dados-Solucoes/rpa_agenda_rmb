import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import crypto from 'crypto'
import nodemailer from 'nodemailer'

/**
 * POST /api/auth/esqueci-senha
 * Gera token de reset e envia email com link
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email } = body

    if (!email) {
      return NextResponse.json(
        { error: 'Email é obrigatório' },
        { status: 400 }
      )
    }

    // Buscar usuário
    const usuario = await prisma.usuario.findUnique({
      where: { email: email.toLowerCase() },
    })

    // Por segurança, não revelar se o email existe ou não
    // Sempre retornar sucesso, mas só enviar email se o usuário existir
    if (!usuario || !usuario.ativo) {
      // Retornar sucesso mesmo se não encontrar (por segurança)
      return NextResponse.json({
        message: 'Se o email estiver cadastrado, você receberá as instruções.',
      })
    }

    // Gerar token seguro
    const resetToken = crypto.randomBytes(32).toString('hex')
    const resetTokenExpires = new Date()
    resetTokenExpires.setHours(resetTokenExpires.getHours() + 1) // Válido por 1 hora

    // Salvar token no banco
    await prisma.usuario.update({
      where: { id: usuario.id },
      data: {
        reset_token: resetToken,
        reset_token_expires: resetTokenExpires,
      },
    })

    // Criar link de reset
    // Usar HTTPS em produção, HTTP apenas em desenvolvimento local
    const baseUrl = process.env.NEXTAUTH_URL || (process.env.NODE_ENV === 'production' ? 'https://advromas.precisionsolucoes.com' : 'http://localhost:3000')
    const resetUrl = `${baseUrl}/redefinir-senha?token=${resetToken}`

    // Configurar transporter de email
    // Priorizar Office 365 se as credenciais estiverem configuradas
    const office365Email = process.env.OFFICE365_EMAIL || ''
    const office365Password = process.env.OFFICE365_PASSWORD || ''
    
    let transporter: nodemailer.Transporter | null = null
    let smtpFrom = ''
    
    // Se tiver credenciais do Office 365, usar
    if (office365Email && office365Password) {
      const smtpServer = process.env.SMTP_SERVER || 'smtp-mail.outlook.com'
      const smtpPort = parseInt(process.env.SMTP_PORT || '587')
      
      transporter = nodemailer.createTransport({
        host: smtpServer,
        port: smtpPort,
        secure: smtpPort === 465,
        auth: {
          user: office365Email,
          pass: office365Password,
        },
        tls: {
          ciphers: 'SSLv3',
          rejectUnauthorized: false, // Para Office 365
        },
      })
      smtpFrom = office365Email
    } else {
      // Fallback para Gmail ou SMTP genérico
      const smtpHost = process.env.SMTP_HOST || 'smtp.gmail.com'
      const smtpPort = parseInt(process.env.SMTP_PORT || '587')
      const smtpUser = process.env.SMTP_USER || ''
      const smtpPass = process.env.SMTP_PASS || ''
      smtpFrom = process.env.SMTP_FROM || smtpUser

      // Se não houver configuração SMTP, apenas logar (para desenvolvimento)
      if (!smtpUser || !smtpPass) {
        console.log('⚠️ SMTP não configurado. Link de reset:', resetUrl)
        return NextResponse.json({
          message: 'Se o email estiver cadastrado, você receberá as instruções.',
          // Em desenvolvimento, retornar o link (remover em produção)
          ...(process.env.NODE_ENV === 'development' && { resetUrl }),
        })
      }

      transporter = nodemailer.createTransport({
        host: smtpHost,
        port: smtpPort,
        secure: smtpPort === 465,
        auth: {
          user: smtpUser,
          pass: smtpPass,
        },
      })
    }

    // Enviar email
    try {

      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #1e40af; color: white; padding: 20px; text-align: center; }
            .content { background-color: #f9fafb; padding: 30px; }
            .button { display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>Portal de Análises</h1>
              <p>Advocacia Roberto Matos de Brito</p>
            </div>
            <div class="content">
              <h2>Redefinição de Senha</h2>
              <p>Olá ${usuario.nome},</p>
              <p>Você solicitou a redefinição de senha para sua conta no Portal de Análises.</p>
              <p>Clique no botão abaixo para redefinir sua senha:</p>
              <p style="text-align: center;">
                <a href="${resetUrl}" class="button">Redefinir Senha</a>
              </p>
              <p>Ou copie e cole o link abaixo no seu navegador:</p>
              <p style="word-break: break-all; color: #2563eb;">${resetUrl}</p>
              <p><strong>Este link expira em 1 hora.</strong></p>
              <p>Se você não solicitou esta redefinição, ignore este email.</p>
            </div>
            <div class="footer">
              <p>Este é um email automático, por favor não responda.</p>
            </div>
          </div>
        </body>
        </html>
      `

      await transporter.sendMail({
        from: smtpFrom,
        to: usuario.email,
        subject: 'Redefinição de Senha - Portal de Análises',
        html: htmlContent,
      })

      console.log(`✅ Email de reset enviado para ${usuario.email}`)
    } catch (emailError) {
      console.error('Erro ao enviar email:', emailError)
      // Continuar mesmo se o email falhar (por segurança)
    }

    return NextResponse.json({
      message: 'Se o email estiver cadastrado, você receberá as instruções.',
    })
  } catch (error) {
    console.error('Erro ao processar solicitação de reset:', error)
    return NextResponse.json(
      {
        error: 'Erro ao processar solicitação',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    )
  }
}
