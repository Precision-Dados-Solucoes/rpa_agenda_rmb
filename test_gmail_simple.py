#!/usr/bin/env python3
"""
Script simples para teste de e-mail Gmail
Execute este script para testar o envio de e-mail
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl

def send_test_email():
    """
    Envia e-mail de teste via Gmail
    """
    print("📧 TESTE DE ENVIO DE E-MAIL VIA GMAIL")
    print("="*50)
    
    # CONFIGURE AQUI SUAS CREDENCIAIS
    sender_email = "cleiton.precisionsolucoes@gmail.com"
    sender_password = "SUA_SENHA_DE_APP_AQUI"  # Substitua pela senha de app do Gmail
    
    recipient_email = "cleiton.sanches@precisionsolucoes.com"
    
    # Verificar se a senha foi configurada
    if sender_password == "SUA_SENHA_DE_APP_AQUI":
        print("⚠️  CONFIGURE A SENHA DE APP DO GMAIL!")
        print("🔧 Para obter a senha de app:")
        print("   1. Acesse: https://myaccount.google.com/security")
        print("   2. Ative a verificação em 2 etapas")
        print("   3. Gere uma senha de app para 'Outro'")
        print("   4. Substitua 'SUA_SENHA_DE_APP_AQUI' pela senha gerada")
        return False
    
    # Configurações
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Assunto e corpo
    subject = f"🧪 Teste RPA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    body = f"""
    <html>
    <body>
        <h2>🧪 Teste de E-mail - RPA Agenda RMB</h2>
        <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Status:</strong> ✅ E-mail enviado com sucesso!</p>
        <p><strong>De:</strong> {sender_email}</p>
        <p><strong>Para:</strong> {recipient_email}</p>
        
        <hr>
        <p><em>Este é um e-mail de teste automático do sistema RPA Agenda RMB.</em></p>
        <p><em>Se você recebeu este e-mail, a configuração está funcionando!</em></p>
    </body>
    </html>
    """
    
    try:
        print(f"📧 Enviando e-mail...")
        print(f"   De: {sender_email}")
        print(f"   Para: {recipient_email}")
        
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Adicionar corpo HTML
        html_part = MIMEText(body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Conectar e enviar
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print("✅ E-mail enviado com sucesso!")
        print("📧 Verifique sua caixa de entrada (e spam)")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTE DE E-MAIL")
    print("="*40)
    
    success = send_test_email()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ TESTE FALHOU!")
        print("🔧 Verifique as configurações e tente novamente")