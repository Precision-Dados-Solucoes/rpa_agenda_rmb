import nodemailer from 'nodemailer'

/**
 * Configura e retorna o transporter de email
 * Suporta Office 365 e Gmail
 */
function getEmailTransporter() {
  // Priorizar Office 365 se as credenciais estiverem configuradas
  const office365Email = process.env.OFFICE365_EMAIL || ''
  const office365Password = process.env.OFFICE365_PASSWORD || ''
  
  // Se tiver credenciais do Office 365, usar
  if (office365Email && office365Password) {
    const smtpServer = process.env.SMTP_SERVER || 'smtp-mail.outlook.com'
    const smtpPort = parseInt(process.env.SMTP_PORT || '587')
    
    return nodemailer.createTransport({
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
  }
  
  // Fallback para Gmail ou SMTP genérico
  const smtpHost = process.env.SMTP_HOST || 'smtp.gmail.com'
  const smtpPort = parseInt(process.env.SMTP_PORT || '587')
  const smtpUser = process.env.SMTP_USER || ''
  const smtpPass = process.env.SMTP_PASS || ''

  if (!smtpUser || !smtpPass) {
    return null
  }

  return nodemailer.createTransport({
    host: smtpHost,
    port: smtpPort,
    secure: smtpPort === 465,
    auth: {
      user: smtpUser,
      pass: smtpPass,
    },
  })
}

/**
 * Envia email de boas-vindas para novo usuário
 */
export async function enviarEmailBoasVindas(
  email: string,
  nome: string,
  senha: string
): Promise<boolean> {
  try {
    const transporter = getEmailTransporter()
    
    if (!transporter) {
      console.log('⚠️ SMTP não configurado. Email de boas-vindas não enviado.')
      console.log('💡 Configure OFFICE365_EMAIL e OFFICE365_PASSWORD ou SMTP_USER e SMTP_PASS')
      console.log(`📧 Dados do novo usuário: ${nome} (${email}) - Senha: ${senha}`)
      return false
    }

    const baseUrl = process.env.NEXTAUTH_URL || 
      (process.env.NODE_ENV === 'production' 
        ? 'https://advromas.precisionsolucoes.com' 
        : 'http://localhost:3000')
    
    const loginUrl = `${baseUrl}/login`

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background-color: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
          .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .credentials { background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }
          .credentials strong { color: #1e40af; }
          .button { display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
          .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
          .warning { background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Portal de Análises</h1>
            <p>Advocacia Roberto Matos de Brito</p>
          </div>
          <div class="content">
            <h2>Bem-vindo ao Portal de Análises!</h2>
            <p>Olá <strong>${nome}</strong>,</p>
            <p>Sua conta foi criada com sucesso no Portal de Análises. Você já pode acessar o sistema usando as credenciais abaixo:</p>
            
            <div class="credentials">
              <p><strong>Email:</strong> ${email}</p>
              <p><strong>Senha temporária:</strong> ${senha}</p>
            </div>

            <p style="text-align: center;">
              <a href="${loginUrl}" class="button">Acessar Portal</a>
            </p>

            <div class="warning">
              <p><strong>⚠️ Importante:</strong></p>
              <p>Por questões de segurança, você será solicitado a alterar sua senha no primeiro acesso.</p>
              <p>Guarde estas credenciais em local seguro até realizar o primeiro login.</p>
            </div>

            <p>Se você tiver alguma dúvida ou precisar de ajuda, entre em contato com o administrador do sistema.</p>
          </div>
          <div class="footer">
            <p>Este é um email automático, por favor não responda.</p>
            <p>Portal de Análises - Advocacia Roberto Matos de Brito</p>
          </div>
        </div>
      </body>
      </html>
    `

    // Determinar remetente (priorizar Office 365, depois SMTP genérico)
    const smtpFrom = process.env.OFFICE365_EMAIL || 
                     process.env.SMTP_FROM || 
                     process.env.SMTP_USER || 
                     ''

    await transporter.sendMail({
      from: smtpFrom,
      to: email,
      subject: 'Bem-vindo ao Portal de Análises - Suas Credenciais de Acesso',
      html: htmlContent,
    })

    console.log(`✅ Email de boas-vindas enviado para ${email}`)
    return true
  } catch (error) {
    console.error('Erro ao enviar email de boas-vindas:', error)
    return false
  }
}
