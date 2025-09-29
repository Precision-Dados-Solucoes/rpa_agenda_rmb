#!/usr/bin/env python3
"""
Script avançado para envio de e-mail via Gmail
Usa variáveis de ambiente para credenciais
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def send_test_email():
    """
    Envia e-mail de teste via Gmail usando variáveis de ambiente
    """
    print("📧 INICIANDO TESTE DE ENVIO DE E-MAIL VIA GMAIL")
    print("="*60)
    
    # Configurações do Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Credenciais das variáveis de ambiente
    sender_email = os.getenv("GMAIL_USERNAME", "cleiton.precisionsolucoes@gmail.com")
    sender_password = os.getenv("GMAIL_PASSWORD")
    
    # Destinatário
    recipient_email = "cleiton.sanches@precisionsolucoes.com"
    
    # Verificar se as credenciais estão configuradas
    if not sender_password:
        print("❌ ERRO: GMAIL_PASSWORD não configurada!")
        print("🔧 Configure a variável de ambiente GMAIL_PASSWORD")
        print("   Exemplo: export GMAIL_PASSWORD='sua_senha_de_app'")
        return False
    
    # Assunto e corpo do e-mail
    subject = f"🧪 Teste de E-mail - RPA Agenda RMB - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #2c3e50; text-align: center;">🧪 Teste de E-mail - RPA Agenda RMB</h2>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>📅 Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p><strong>✅ Status:</strong> E-mail enviado com sucesso!</p>
                <p><strong>⚙️ Configuração:</strong> Gmail SMTP funcionando corretamente</p>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0;">✅ Sistema Funcionando</h3>
                <p>Este e-mail confirma que:</p>
                <ul>
                    <li>🔐 Autenticação Gmail está funcionando</li>
                    <li>📧 Envio de e-mails está operacional</li>
                    <li>🤖 Sistema RPA pode enviar notificações</li>
                </ul>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            
            <p style="color: #666; font-size: 12px; text-align: center;">
                <em>Este é um e-mail de teste automático do sistema RPA Agenda RMB.</em><br>
                <em>Se você recebeu este e-mail, a configuração está funcionando perfeitamente!</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        print(f"📧 Configurando envio de e-mail...")
        print(f"   De: {sender_email}")
        print(f"   Para: {recipient_email}")
        print(f"   Assunto: {subject}")
        
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Adicionar corpo HTML
        html_part = MIMEText(body, 'html', 'utf-8')
        msg.attach(html_part)
        
        print("🔐 Conectando ao servidor SMTP do Gmail...")
        
        # Criar contexto SSL
        context = ssl.create_default_context()
        
        # Conectar ao servidor SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("🔒 Iniciando conexão segura (TLS)...")
            server.starttls(context=context)
            
            print("🔑 Fazendo login no Gmail...")
            server.login(sender_email, sender_password)
            
            print("📤 Enviando e-mail...")
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            
        print("✅ E-mail enviado com sucesso!")
        print(f"📧 Destinatário: {recipient_email}")
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erro de autenticação: {e}")
        print("🔧 Verifique:")
        print("   - E-mail e senha estão corretos")
        print("   - Senha de app está habilitada no Gmail")
        print("   - Verificação em 2 etapas está ativada")
        print("   - GMAIL_PASSWORD está configurada corretamente")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Erro SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """
    Função principal
    """
    print("🚀 TESTE DE ENVIO DE E-MAIL VIA GMAIL")
    print("="*50)
    
    # Verificar variáveis de ambiente
    gmail_username = os.getenv("GMAIL_USERNAME")
    gmail_password = os.getenv("GMAIL_PASSWORD")
    
    print(f"🔍 Verificando configurações:")
    print(f"   GMAIL_USERNAME: {'✅ Configurado' if gmail_username else '❌ Não configurado'}")
    print(f"   GMAIL_PASSWORD: {'✅ Configurado' if gmail_password else '❌ Não configurado'}")
    
    if not gmail_username or not gmail_password:
        print("\n⚠️  CONFIGURAÇÃO NECESSÁRIA:")
        print("🔧 Configure as variáveis de ambiente:")
        print("   export GMAIL_USERNAME='seu_email@gmail.com'")
        print("   export GMAIL_PASSWORD='sua_senha_de_app'")
        print("\n📋 Para obter a senha de app do Gmail:")
        print("   1. Acesse: https://myaccount.google.com/security")
        print("   2. Ative a verificação em 2 etapas")
        print("   3. Gere uma senha de app para 'Outro'")
        print("   4. Use essa senha na variável GMAIL_PASSWORD")
        return
    
    # Executar teste
    success = send_test_email()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("📧 Verifique sua caixa de entrada (e spam)")
        print("✅ Sistema de e-mail está funcionando perfeitamente!")
    else:
        print("\n❌ TESTE FALHOU!")
        print("🔧 Verifique as configurações e tente novamente")

if __name__ == "__main__":
    main()
