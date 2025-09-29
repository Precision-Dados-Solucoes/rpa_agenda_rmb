#!/usr/bin/env python3
"""
Script de teste para envio de e-mail via Gmail
Envia e-mail de teste para verificar configuração
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import ssl

def send_test_email():
    """
    Envia e-mail de teste via Gmail
    """
    print("📧 INICIANDO TESTE DE ENVIO DE E-MAIL VIA GMAIL")
    print("="*60)
    
    # Configurações do Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Credenciais (configure estas variáveis)
    sender_email = "cleiton.precisionsolucoes@gmail.com"  # Seu e-mail Gmail
    sender_password = "sua_senha_de_app_aqui"  # Senha de app do Gmail
    
    # Destinatário
    recipient_email = "cleiton.sanches@precisionsolucoes.com"
    
    # Assunto e corpo do e-mail
    subject = f"🧪 Teste de E-mail - RPA Agenda RMB - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    body = f"""
    <html>
    <body>
        <h2>🧪 Teste de E-mail - RPA Agenda RMB</h2>
        <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Status:</strong> ✅ E-mail enviado com sucesso!</p>
        <p><strong>Configuração:</strong> Gmail SMTP funcionando corretamente</p>
        
        <hr>
        <p><em>Este é um e-mail de teste automático do sistema RPA Agenda RMB.</em></p>
        <p><em>Se você recebeu este e-mail, a configuração de envio está funcionando perfeitamente!</em></p>
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
    
    # Verificar se as credenciais estão configuradas
    sender_email = "cleiton.sanches@precisionsolucoes.com"
    sender_password = "sua_senha_de_app_aqui"
    
    if sender_password == "sua_senha_de_app_aqui":
        print("⚠️  ATENÇÃO: Configure a senha de app do Gmail no script!")
        print("🔧 Para obter a senha de app:")
        print("   1. Acesse: https://myaccount.google.com/security")
        print("   2. Ative a verificação em 2 etapas")
        print("   3. Gere uma senha de app para 'Outro'")
        print("   4. Substitua 'sua_senha_de_app_aqui' pela senha gerada")
        print()
        print("📧 Ou configure as variáveis de ambiente:")
        print("   GMAIL_USERNAME=seu_email@gmail.com")
        print("   GMAIL_PASSWORD=sua_senha_de_app")
        return
    
    # Executar teste
    success = send_test_email()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("📧 Verifique sua caixa de entrada (e spam)")
    else:
        print("\n❌ TESTE FALHOU!")
        print("🔧 Verifique as configurações e tente novamente")

if __name__ == "__main__":
    main()