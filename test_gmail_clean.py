#!/usr/bin/env python3
"""
Script simples para teste de e-mail Gmail (sem emojis)
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
    print("TESTE DE ENVIO DE E-MAIL VIA GMAIL")
    print("="*50)
    
    # CONFIGURE AQUI SUAS CREDENCIAIS
    sender_email = "cleiton.precisionsolucoes@gmail.com"
    sender_password = "kpql oddf qnmy lcvc"  # Senha de app do Gmail
    
    recipient_email = "cleiton.sanches@precisionsolucoes.com"
    
    # Configurações
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Assunto e corpo
    subject = f"Teste RPA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    body = f"""
    <html>
    <body>
        <h2>Teste de E-mail - RPA Agenda RMB</h2>
        <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Status:</strong> E-mail enviado com sucesso!</p>
        <p><strong>De:</strong> {sender_email}</p>
        <p><strong>Para:</strong> {recipient_email}</p>
        
        <hr>
        <p><em>Este e um e-mail de teste automatico do sistema RPA Agenda RMB.</em></p>
        <p><em>Se voce recebeu este e-mail, a configuracao esta funcionando!</em></p>
    </body>
    </html>
    """
    
    try:
        print(f"Enviando e-mail...")
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
            print("Conectando ao Gmail...")
            server.starttls(context=context)
            print("Fazendo login...")
            server.login(sender_email, sender_password)
            print("Enviando e-mail...")
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print("SUCCESS: E-mail enviado com sucesso!")
        print("Verifique sua caixa de entrada (e spam)")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERRO de autenticacao: {e}")
        print("Verifique:")
        print("   - E-mail e senha estao corretos")
        print("   - Senha de app esta habilitada no Gmail")
        print("   - Verificacao em 2 etapas esta ativada")
        return False
        
    except smtplib.SMTPException as e:
        print(f"ERRO SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO TESTE DE E-MAIL")
    print("="*40)
    
    success = send_test_email()
    
    if success:
        print("\nTESTE CONCLUIDO COM SUCESSO!")
    else:
        print("\nTESTE FALHOU!")
        print("Verifique as configuracoes e tente novamente")

