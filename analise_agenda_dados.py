#!/usr/bin/env python3
"""
Análise de Dados - Agenda sem Interação
Gera gráficos baseados em itens com status Pendente, sem andamento "1. Produzido"
Data de conclusão prevista: data atual
"""

import asyncio
import asyncpg
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import date, datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import ssl
from dotenv import load_dotenv

# Carregar variáveis de ambiente (apenas se não estiverem definidas)
if not os.getenv("GMAIL_USERNAME"):
    load_dotenv('config.env')


# Configurações do Gmail
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "rmbautomacoes@gmail.com")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
RECIPIENT_EMAILS = [
    "cleiton.sanches@precisionsolucoes.com",
    "controladoria@gestaogt.onmicrosoft.com"
]

# Configurar estilo dos gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

async def connect_to_supabase():
    """
    Conecta ao Supabase usando as credenciais configuradas
    """
    print("Conectando ao Supabase...")
    
    # Credenciais do Supabase das variáveis de ambiente
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "L7CEsmTv@vZKfpN")
    
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
        print("Conexão com Supabase estabelecida!")
        return conn
    except Exception as e:
        print(f"Erro ao conectar com Supabase: {e}")
        return None

async def get_agenda_analysis_data(conn):
    """
    Busca dados para análise: itens com status Pendente, sem andamento "1. Produzido"
    Data de conclusão prevista: data atual
    """
    print("Buscando dados para análise...")
    
    today = date.today()
    
    # Query para buscar dados de análise
    query = """
    SELECT 
        a.id_legalone,
        a.compromisso_tarefa,
        a.executante,
        a.tipo,
        a.subtipo,
        a.etiqueta,
        a.pasta_proc,
        a.cadastro,
        a.conclusao_prevista_data,
        a.descricao
    FROM agenda_base a
    LEFT JOIN andamento_base an ON a.id_legalone = an.id_agenda_legalone 
        AND an.tipo_andamento = '1. Produzido'
    WHERE DATE(a.conclusao_prevista_data) = $1 
    AND a.conclusao_efetiva_data IS NULL
    AND a.status = 'Pendente'
    AND an.id_agenda_legalone IS NULL
    ORDER BY a.conclusao_prevista_data ASC
    """
    
    try:
        rows = await conn.fetch(query, today)
        print(f"Encontrados {len(rows)} itens para análise")
        
        # Converter para DataFrame com nomes de colunas
        if rows:
            df = pd.DataFrame(rows)
            # Renomear colunas para os nomes corretos
            column_names = [
                'id_legalone', 'compromisso_tarefa', 'executante', 'tipo', 'subtipo',
                'etiqueta', 'pasta_proc', 'cadastro', 'conclusao_prevista_data', 'descricao'
            ]
            df.columns = column_names
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

def create_executante_chart(df):
    """
    Cria gráfico por Executante
    """
    if df.empty:
        print("[AVISO] Nenhum dado disponivel para grafico de Executante")
        return
    
    # Contar por executante
    executante_counts = df['executante'].value_counts()
    
    # Criar gráfico
    plt.figure(figsize=(12, 8))
    colors = plt.cm.Set3(range(len(executante_counts)))
    
    bars = plt.bar(range(len(executante_counts)), executante_counts.values, color=colors)
    
    # Personalizar gráfico
    plt.title('Agenda sem Interação - Por Executante\n(Status Pendente, sem andamento "1. Produzido")', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Executante', fontsize=12, fontweight='bold')
    plt.ylabel('Quantidade de Itens', fontsize=12, fontweight='bold')
    
    # Rotacionar labels se necessário
    plt.xticks(range(len(executante_counts)), executante_counts.index, rotation=45, ha='right')
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Salvar grafico
    plt.savefig('grafico_executante.png', dpi=300, bbox_inches='tight')
    print("[OK] Grafico por Executante salvo: grafico_executante.png")
    plt.close()  # Fechar figura para liberar memória

def create_etiqueta_chart(df):
    """
    Cria gráfico por Etiqueta
    """
    if df.empty:
        print("[AVISO] Nenhum dado disponivel para grafico de Etiqueta")
        return
    
    # Contar por etiqueta
    etiqueta_counts = df['etiqueta'].value_counts()
    
    # Criar gráfico de pizza
    plt.figure(figsize=(10, 10))
    colors = plt.cm.Pastel1(range(len(etiqueta_counts)))
    
    wedges, texts, autotexts = plt.pie(etiqueta_counts.values, 
                                      labels=etiqueta_counts.index,
                                      autopct='%1.1f%%',
                                      colors=colors,
                                      startangle=90)
    
    # Personalizar gráfico
    plt.title('Agenda sem Interação - Por Etiqueta\n(Status Pendente, sem andamento "1. Produzido")', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Melhorar legibilidade
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    plt.axis('equal')
    plt.tight_layout()
    
    # Salvar grafico
    plt.savefig('grafico_etiqueta.png', dpi=300, bbox_inches='tight')
    print("[OK] Grafico por Etiqueta salvo: grafico_etiqueta.png")
    plt.close()  # Fechar figura para liberar memória

def create_tipo_subtipo_chart(df):
    """
    Cria gráfico por Tipo/Subtipo
    """
    if df.empty:
        print("[AVISO] Nenhum dado disponivel para grafico de Tipo/Subtipo")
        return
    
    # Combinar tipo e subtipo
    df['tipo_subtipo'] = df['tipo'] + ' | ' + df['subtipo'].fillna('Sem Subtipo')
    
    # Contar por tipo/subtipo
    tipo_counts = df['tipo_subtipo'].value_counts()
    
    # Criar gráfico horizontal
    plt.figure(figsize=(14, 8))
    colors = plt.cm.viridis(range(len(tipo_counts)))
    
    bars = plt.barh(range(len(tipo_counts)), tipo_counts.values, color=colors)
    
    # Personalizar gráfico
    plt.title('Agenda sem Interação - Por Tipo/Subtipo\n(Status Pendente, sem andamento "1. Produzido")', 
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Quantidade de Itens', fontsize=12, fontweight='bold')
    plt.ylabel('Tipo/Subtipo', fontsize=12, fontweight='bold')
    
    # Configurar labels
    plt.yticks(range(len(tipo_counts)), tipo_counts.index)
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                f'{int(width)}', ha='left', va='center', fontweight='bold')
    
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    # Salvar grafico
    plt.savefig('grafico_tipo_subtipo.png', dpi=300, bbox_inches='tight')
    print("[OK] Grafico por Tipo/Subtipo salvo: grafico_tipo_subtipo.png")
    plt.close()  # Fechar figura para liberar memória

def create_summary_dashboard(df):
    """
    Cria dashboard resumo com múltiplos gráficos
    """
    if df.empty:
        print("[AVISO] Nenhum dado disponivel para dashboard")
        return
    
    # Criar figura com subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Dashboard - Análise de Agenda sem Interação\n(Status Pendente, sem andamento "1. Produzido")', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # 1. Gráfico por Executante (barras)
    executante_counts = df['executante'].value_counts()
    ax1.bar(range(len(executante_counts)), executante_counts.values, color='skyblue')
    ax1.set_title('Por Executante', fontweight='bold')
    ax1.set_xlabel('Executante')
    ax1.set_ylabel('Quantidade')
    ax1.set_xticks(range(len(executante_counts)))
    ax1.set_xticklabels(executante_counts.index, rotation=45, ha='right')
    ax1.grid(axis='y', alpha=0.3)
    
    # Adicionar valores
    for i, v in enumerate(executante_counts.values):
        ax1.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    # 2. Gráfico por Etiqueta (pizza)
    etiqueta_counts = df['etiqueta'].value_counts()
    ax2.pie(etiqueta_counts.values, labels=etiqueta_counts.index, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Por Etiqueta', fontweight='bold')
    
    # 3. Gráfico por Tipo (barras horizontais)
    tipo_counts = df['tipo'].value_counts()
    ax3.barh(range(len(tipo_counts)), tipo_counts.values, color='lightcoral')
    ax3.set_title('Por Tipo', fontweight='bold')
    ax3.set_xlabel('Quantidade')
    ax3.set_ylabel('Tipo')
    ax3.set_yticks(range(len(tipo_counts)))
    ax3.set_yticklabels(tipo_counts.index)
    ax3.grid(axis='x', alpha=0.3)
    
    # Adicionar valores
    for i, v in enumerate(tipo_counts.values):
        ax3.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    # 4. Resumo estatístico
    ax4.axis('off')
    stats_text = f"""
    📊 RESUMO ESTATÍSTICO
    
    📅 Data de Análise: {date.today().strftime('%d/%m/%Y')}
    
    📈 Total de Itens: {len(df)}
    
    👥 Executantes: {df['executante'].nunique()}
    
    🏷️ Etiquetas: {df['etiqueta'].nunique()}
    
    📋 Tipos: {df['tipo'].nunique()}
    
    📁 Pastas: {df['pasta_proc'].nunique()}
    
    ⚠️ Critério: Status Pendente
    ❌ Sem andamento "1. Produzido"
    📅 Data conclusão: Hoje
    """
    
    ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=12,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    plt.tight_layout()
    
    # Salvar dashboard
    plt.savefig('dashboard_analise_agenda.png', dpi=300, bbox_inches='tight')
    print("[OK] Dashboard resumo salvo: dashboard_analise_agenda.png")
    plt.close()  # Fechar figura para liberar memória

def send_analysis_email(df):
    """
    Envia os gráficos de análise por email
    """
    print("[INFO] Enviando analise por email...")
    
    
    today = date.today()
    subject = f"Análise de agenda diária - {today.strftime('%d/%m/%Y')}"
    
    # Criar mensagem
    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_USERNAME
    msg['To'] = ", ".join(RECIPIENT_EMAILS)
    msg['Subject'] = subject
    
    # Criar conteúdo HTML do email
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50; text-align: center;">Análise de Agenda Diária</h2>
            <p style="text-align: center; color: #666;">{today.strftime('%d/%m/%Y')}</p>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0; font-family: Calibri, Arial, sans-serif;">Resumo da Análise</h3>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Total de itens analisados:</strong> {len(df)}</p>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Executantes únicos:</strong> {df['executante'].nunique()}</p>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Etiquetas únicas:</strong> {df['etiqueta'].nunique()}</p>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Tipos únicos:</strong> {df['tipo'].nunique()}</p>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Critério:</strong> Status Pendente, sem andamento "1. Produzido"</p>
                <p style="font-family: Calibri, Arial, sans-serif; font-size: 13px; margin: 5px 0; line-height: 1.3;"><strong>Data de conclusão:</strong> {today.strftime('%d/%m/%Y')}</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">================================</p>
            </div>
            
            <h3 style="color: #2c3e50;">Gráficos de Análise</h3>
            
            <!-- Gráfico por Executante -->
            <div style="margin: 30px 0; text-align: center;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">👥 Distribuição por Executante</h4>
                <img src="cid:grafico_executante" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            </div>
            
            <!-- Gráfico por Etiqueta -->
            <div style="margin: 30px 0; text-align: center;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">🏷️ Distribuição por Etiqueta</h4>
                <img src="cid:grafico_etiqueta" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            </div>
            
            <!-- Gráfico por Tipo/Subtipo -->
            <div style="margin: 30px 0; text-align: center;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">📋 Distribuição por Tipo/Subtipo</h4>
                <img src="cid:grafico_tipo_subtipo" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            </div>
            
            <!-- Dashboard Resumo -->
            <div style="margin: 30px 0; text-align: center;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">📊 Dashboard Resumo</h4>
                <img src="cid:dashboard_analise_agenda" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p style="margin: 0; font-size: 14px; color: #856404; font-family: Calibri, Arial, sans-serif;">
                    <strong>📎 Nota:</strong> Se as imagens não aparecerem acima, verifique os anexos do email. 
                    Os gráficos também foram enviados como anexos para garantir a visualização completa.
                </p>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #666;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">================================</p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px; text-align: center;">
                <em>Análise automática do sistema RPA Agenda RMB</em><br>
                <em>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Adicionar corpo HTML
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    # Incorporar gráficos no corpo do email + anexar como backup
    image_files = {
        'grafico_executante.png': 'grafico_executante',
        'grafico_etiqueta.png': 'grafico_etiqueta', 
        'grafico_tipo_subtipo.png': 'grafico_tipo_subtipo',
        'dashboard_analise_agenda.png': 'dashboard_analise_agenda'
    }
    
    for image_file, cid_name in image_files.items():
        if os.path.exists(image_file):
            with open(image_file, 'rb') as f:
                img_data = f.read()
                
                # Incorporar no corpo (para clientes que suportam)
                image_inline = MIMEImage(img_data)
                image_inline.add_header('Content-ID', f'<{cid_name}>')
                image_inline.add_header('Content-Disposition', 'inline')
                msg.attach(image_inline)
                
                # Anexar como backup (para clientes que bloqueiam imagens)
                image_attachment = MIMEImage(img_data)
                image_attachment.add_header('Content-Disposition', f'attachment; filename={image_file}')
                msg.attach(image_attachment)
                
                print(f"[OK] Incorporado e anexado: {image_file}")
        else:
            print(f"[AVISO] Arquivo nao encontrado: {image_file}")
    
    try:
        # Conectar e enviar
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USERNAME, RECIPIENT_EMAILS, msg.as_string())
        
        print(f"[OK] E-mail enviado com sucesso para {len(RECIPIENT_EMAILS)} destinatarios")
        print(f"[INFO] Destinatarios: {', '.join(RECIPIENT_EMAILS)}")
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao enviar e-mail: {e}")
        return False

async def main():
    """
    Função principal
    """
    print("ANÁLISE DE DADOS - AGENDA SEM INTERAÇÃO")
    print("="*60)
    
    # Conectar ao Supabase
    conn = await connect_to_supabase()
    if not conn:
        print("[ERRO] Falha na conexao com Supabase. Abortando...")
        return
    
    try:
        # Buscar dados
        df = await get_agenda_analysis_data(conn)
        
        if df.empty:
            print("[ERRO] Nenhum dado encontrado para analise")
            print("[INFO] Verifique se ha itens com status Pendente e data de conclusao para hoje")
            return
        
        print(f"[OK] {len(df)} itens encontrados para analise")
        
        # Verificar colunas disponíveis
        print(f"[INFO] Colunas disponíveis: {list(df.columns)}")
        
        # Criar graficos
        print("\n[INFO] Gerando graficos...")
        
        # 1. Grafico por Executante
        print("1. Criando grafico por Executante...")
        create_executante_chart(df)
        
        # 2. Grafico por Etiqueta
        print("2. Criando grafico por Etiqueta...")
        create_etiqueta_chart(df)
        
        # 3. Grafico por Tipo/Subtipo
        print("3. Criando grafico por Tipo/Subtipo...")
        create_tipo_subtipo_chart(df)
        
        # 4. Dashboard resumo
        print("4. Criando dashboard resumo...")
        create_summary_dashboard(df)
        
        # 5. Enviar por email
        print("5. Enviando analise por email...")
        email_success = send_analysis_email(df)
        
        print("\n[OK] Analise concluida com sucesso!")
        print("[INFO] Arquivos gerados:")
        print("   - grafico_executante.png")
        print("   - grafico_etiqueta.png")
        print("   - grafico_tipo_subtipo.png")
        print("   - dashboard_analise_agenda.png")
        
        if email_success:
            print("[OK] E-mail enviado com sucesso!")
        else:
            print("[AVISO] Falha no envio do e-mail, mas os graficos foram gerados")
        
    finally:
        await conn.close()
        print("Conexão com Supabase fechada")

if __name__ == "__main__":
    asyncio.run(main())
