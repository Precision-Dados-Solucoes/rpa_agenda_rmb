#!/usr/bin/env python3
"""
Script para enviar relatório diário de agendamentos
Consulta Supabase e envia e-mail com novos agendamentos do dia
"""
import asyncio
import asyncpg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import ssl
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Gmail
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "cleiton.precisionsolucoes@gmail.com")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "kpql oddf qnmy lcvc")
RECIPIENT_EMAILS = [
    "cleiton.sanches@precisionsolucoes.com",
    "controladoria@gestaogt.onmicrosoft.com"
]

async def connect_to_supabase():
    """
    Conecta ao Supabase usando as credenciais configuradas
    """
    print("Conectando ao Supabase...")
    
    # Credenciais do Supabase (hardcoded para teste)
    host = "db.dhfmqumwizrwdbjnbcua.supabase.co"
    port = "5432"
    database = "postgres"
    user = "postgres"
    password = "L7CEsmTv@vZKfpN"
    
    print(f"Conectando: {user}@{host}:{port}/{database}")
    
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            ssl="require"
        )
        print("Conexao com Supabase estabelecida!")
        return conn
    except Exception as e:
        print(f"Erro ao conectar com Supabase: {e}")
        return None

async def get_daily_agenda_data(conn):
    """
    Busca agendamentos do dia com status 'Pendente'
    """
    print("Buscando agendamentos do dia...")
    
    today = date.today()
    
    query = """
    SELECT 
        id_legalone,
        compromisso_tarefa,
        executante,
        tipo,
        subtipo,
        etiqueta,
        pasta_proc,
        cadastro,
        conclusao_prevista_data,
        descricao,
        link
    FROM agenda_base 
    WHERE DATE(cadastro) = $1 
    AND status = 'Pendente'
    ORDER BY cadastro DESC
    """
    
    try:
        rows = await conn.fetch(query, today)
        print(f"Encontrados {len(rows)} agendamentos do dia")
        return rows
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []

def format_agenda_item(item, is_last=False):
    """
    Formata um item de agendamento para o e-mail
    """
    tipo_subtipo = f"{item['tipo']} | {item['subtipo']}" if item['subtipo'] else item['tipo']
    
    separator = "" if is_last else """
    <div style="text-align: center; margin: 15px 0; color: #666;">
        <p style="margin: 0; font-family: monospace; font-size: 12px;">--------------------------------</p>
    </div>
    """
    
    return f"""
    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; background-color: #f9f9f9; font-family: Calibri, Arial, sans-serif;">
        <h3 style="color: #2c3e50; margin-top: 0; font-family: Calibri, Arial, sans-serif;">{item['compromisso_tarefa'] or 'N/A'}</h3>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Executante:</strong> <strong>{item['executante'] or 'N/A'}</strong></p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Id da Agenda:</strong> {item['id_legalone'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Tipo / Subtipo:</strong> {tipo_subtipo}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Etiqueta:</strong> {item['etiqueta'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Pasta vinculada:</strong> {item['pasta_proc'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Data do cadastro:</strong> {item['cadastro'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Data de conclusao prevista:</strong> {item['conclusao_prevista_data'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Descricao:</strong> {item['descricao'] or 'N/A'}</p>
        <p style="font-family: Calibri, Arial, sans-serif;"><strong>Link:</strong> <a href="{item['link'] or '#'}" target="_blank" style="font-family: Calibri, Arial, sans-serif;">{item['link'] or 'N/A'}</a></p>
    </div>
    {separator}
    """

def create_email_content(agenda_items):
    """
    Cria o conteúdo do e-mail com os agendamentos
    """
    today = date.today()
    subject = f"Novos agendamentos do dia {today.strftime('%d/%m/%Y')}"
    
    # Cabeçalho do e-mail
    header = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50; text-align: center;">Novos Agendamentos do Dia</h2>
            <p style="text-align: center; color: #666;">{today.strftime('%d/%m/%Y')}</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
                <p style="margin: 0; font-size: 16px; color: #333;">
                    Aqui estão os novos agendamentos realizados pela equipe de controladoria hoje, até as 17:29h.<br>
                    Qualquer dúvida, seguir o procedimento padrão.
                </p>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                <hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">--------------------------------</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">================================</p>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0;">Resumo</h3>
                <p><strong>Total de agendamentos:</strong> {len(agenda_items)}</p>
                <p><strong>Status:</strong> Pendente</p>
                <p><strong>Data de consulta:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">================================</p>
            </div>
    """
    
    # Conteúdo dos agendamentos
    content = header
    
    if agenda_items:
        content += "<h3>Detalhes dos Agendamentos:</h3>"
        for i, item in enumerate(agenda_items):
            is_last = (i == len(agenda_items) - 1)
            content += format_agenda_item(item, is_last)
    else:
        content += """
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">Nenhum agendamento encontrado</h3>
            <p>Não foram encontrados agendamentos pendentes para o dia de hoje.</p>
        </div>
        """
    
    # Rodapé
    footer = f"""
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                <em>Relatorio automatico do sistema RPA Agenda RMB</em><br>
                <em>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    content += footer
    return subject, content

def send_email(subject, content):
    """
    Envia o e-mail com o relatório para múltiplos destinatários
    """
    print("Enviando e-mail...")
    
    try:
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USERNAME
        msg['To'] = ", ".join(RECIPIENT_EMAILS)
        msg['Subject'] = subject
        
        # Adicionar corpo HTML
        html_part = MIMEText(content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Conectar e enviar
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USERNAME, RECIPIENT_EMAILS, msg.as_string())
        
        print(f"E-mail enviado com sucesso para {len(RECIPIENT_EMAILS)} destinatários!")
        print(f"Destinatários: {', '.join(RECIPIENT_EMAILS)}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

async def main():
    """
    Função principal
    """
    print("RELATORIO DIARIO DE AGENDAMENTOS")
    print("="*50)
    
    # Conectar ao Supabase
    conn = await connect_to_supabase()
    if not conn:
        print("Falha na conexao com Supabase. Abortando...")
        return
    
    try:
        # Buscar dados
        agenda_items = await get_daily_agenda_data(conn)
        
        # Criar conteúdo do e-mail
        subject, content = create_email_content(agenda_items)
        
        # Enviar e-mail
        success = send_email(subject, content)
        
        if success:
            print(f"Relatorio enviado com sucesso!")
            print(f"Total de agendamentos: {len(agenda_items)}")
        else:
            print("Falha ao enviar relatorio")
            
    finally:
        await conn.close()
        print("Conexao com Supabase fechada")

if __name__ == "__main__":
    asyncio.run(main())
