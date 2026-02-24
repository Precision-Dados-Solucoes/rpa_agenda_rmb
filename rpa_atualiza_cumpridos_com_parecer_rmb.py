#!/usr/bin/env python3
"""
RPA para Atualização de Cumpridos com Parecer RMB
Automatiza a extração do relatório de atualização de cumpridos com parecer do Legal One/Novajus
URL: https://robertomatos.novajus.com.br/agenda/GenericReport/?id=674
Arquivo esperado: z-rpa_atualiza_cumpridos_com_parecer_rmb_queeue.xlsx
Processamento: UPDATE na tabela agenda_base usando id_legalone como chave
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv
import psycopg2
import asyncpg
from hostinger_mysql_helper import upsert_agenda_base as upsert_agenda_base_hostinger

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None  # type: ignore

# Carrega as variáveis de ambiente do arquivo config.env
load_dotenv('config.env')

# Configuração automática do modo headless baseada no ambiente

# --- Configuração da pasta de downloads ---
downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
print(f"A pasta de downloads será: {os.path.abspath(downloads_dir)}")

async def close_any_known_popup(page):
    """
    Tenta fechar popups modais ou overlays usando seletores comuns para botões de fechar.
    Retorna True se um popup foi encontrado e tentado fechar, False caso contrário.
    """
    close_selectors = [
        '[aria-label="Close"]',          # Botão genérico de fechar (com label ARIA)
        'button:has-text("Fechar")',     # Botão com texto "Fechar"
        'button:has-text("OK")',         # Às vezes "OK" fechar um aviso
        'button.close',                  # Classe comum para botões de fechar
        '.modal-footer button:has-text("Fechar")', # Botão "Fechar" no rodapé de um modal
        '.modal-header button.close',    # Botão "Fechar" no cabeçalho de um modal
        '.popup-close',                  # Classe específica para fechar popups
        '#close-button',                 # ID comum para um botão de fechar
        '[role="dialog"] button:has-text("Fechar")' # Botão fechar dentro de um elemento com role="dialog"
    ]

    print("Tentando fechar popups (se houver)...")
    for selector in close_selectors:
        try:
            element = page.locator(selector)
            if await element.is_visible(timeout=1000):
                print(f"  Popup detectado com seletor: {selector}. Tentando fechar...")
                await element.click(timeout=3000)
                print(f"  Popup fechado com sucesso usando seletor: {selector}.")
                await page.wait_for_timeout(500)
                return True
        except TimeoutError:
            pass
        except Exception as e:
            print(f"  Erro inesperado ao tentar fechar popup com seletor {selector}: {e}")
            pass
    print("Nenhum popup conhecido encontrado ou fechado.")
    return False

def read_excel_file(file_path):
    """
    Lê um arquivo Excel (ou CSV) e retorna um DataFrame do pandas.
    """
    print(f"Lendo o arquivo: {file_path}")
    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, forneça um arquivo .xlsx ou .csv")
        
        print(f"Arquivo '{file_path}' lido com sucesso.")
        print("Primeiras 5 linhas do DataFrame:")
        print(df.head())
        print(f"Colunas do DataFrame: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None

async def process_excel_file(file_path):
    """
    Processa o arquivo Excel baixado com todos os tratamentos necessários.
    """
    print("🔄 Iniciando processamento do arquivo Excel...")
    
    # 1. Ler o arquivo
    df = read_excel_file(file_path)
    if df is None or df.empty:
        print("❌ Erro: Não foi possível ler o arquivo ou arquivo vazio.")
        return None
    
    print(f"📊 Arquivo lido com sucesso. Linhas: {len(df)}")
    
    try:
        # 2. Criar DataFrame processado com as colunas do Supabase
        df_processed = pd.DataFrame()
        
        # Mapeamento direto (sem tratamento)
        direct_mappings = {
            'id_legalone': 'id_legalone',
            'compromisso_tarefa': 'compromisso_tarefa', 
            'tipo': 'tipo',
            'subtipo': 'subtipo',
            'etiqueta': 'etiqueta',
            'pasta_proc': 'Pasta_proc',
            'numero_cnj': 'numero_cnj',
            'executante': 'executante',
            'executante_sim': 'executante_sim',
            'descricao': 'descricao',
            'status': 'status'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"✅ Coluna '{excel_col}' → '{supabase_col}'")
            else:
                print(f"⚠️ Coluna '{excel_col}' não encontrada no arquivo")
                df_processed[supabase_col] = None
        
        # 3. Tratamento de campos de data/hora
        print("🔄 Processando campos de data/hora...")
        
        # Tratar campo 'inicio' (dd/mm/aaaa hh:mm:ss)
        if 'inicio' in df.columns:
            df_processed['inicio_data'] = df['inicio'].apply(extract_date_from_datetime)
            df_processed['inicio_hora'] = df['inicio'].apply(extract_time_from_datetime)
            print("✅ Campo 'inicio' processado → 'inicio_data' e 'inicio_hora'")
        
        # Tratar campo 'conclusao_prevista' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_prevista' in df.columns:
            df_processed['conclusao_prevista_data'] = df['conclusao_prevista'].apply(extract_date_from_datetime)
            df_processed['conclusao_prevista_hora'] = df['conclusao_prevista'].apply(extract_time_from_datetime)
            print("✅ Campo 'conclusao_prevista' processado → 'conclusao_prevista_data' e 'conclusao_prevista_hora'")
        
        # Tratar campo 'conclusao_efetiva' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_efetiva' in df.columns:
            df_processed['conclusao_efetiva_data'] = df['conclusao_efetiva'].apply(extract_date_from_datetime)
            print("✅ Campo 'conclusao_efetiva' processado → 'conclusao_efetiva_data'")
        else:
            # Se não existe campo 'conclusao_efetiva', criar coluna vazia
            df_processed['conclusao_efetiva_data'] = None
            print("⚠️ Campo 'conclusao_efetiva' não encontrado, criando coluna vazia")
        
        # Preencher conclusao_efetiva_data com conclusao_prevista_data quando vazia
        if 'conclusao_prevista_data' in df_processed.columns and 'conclusao_efetiva_data' in df_processed.columns:
            # Usar conclusao_prevista_data onde conclusao_efetiva_data está vazia
            mask = df_processed['conclusao_efetiva_data'].isna() | (df_processed['conclusao_efetiva_data'] == '')
            df_processed.loc[mask, 'conclusao_efetiva_data'] = df_processed.loc[mask, 'conclusao_prevista_data']
            print("✅ Campo 'conclusao_efetiva_data' preenchido com 'conclusao_prevista_data' onde estava vazio")
        
        # Tratar campo 'cadastro' (dd/mm/aaaa hh:mm:ss) → formato aaaa/mm/dd
        if 'cadastro' in df.columns:
            df_processed['cadastro'] = df['cadastro'].apply(extract_date_from_datetime)
            print("✅ Campo 'cadastro' processado → formato aaaa/mm/dd")
        
        # Tratar campo 'prazo_fatal' (dd/mm/aaaa hh:mm) → apenas data
        if 'prazo_fatal' in df.columns:
            df_processed['prazo_fatal_data'] = df['prazo_fatal'].apply(extract_date_from_datetime)
            print("✅ Campo 'prazo_fatal' processado → 'prazo_fatal_data'")
        
        # 4. Gerar campo 'link' concatenado
        if 'id_legalone' in df_processed.columns:
            df_processed['link'] = df_processed['id_legalone'].apply(generate_link)
            print("✅ Campo 'link' gerado com sucesso")
        
        # 5. Filtrar apenas linhas onde executante_sim = "Sim"
        print("🔄 Filtrando linhas onde executante_sim = 'Sim'...")
        if 'executante_sim' in df_processed.columns:
            linhas_antes = len(df_processed)
            df_processed = df_processed[df_processed['executante_sim'] == 'Sim']
            linhas_depois = len(df_processed)
            print(f"✅ Filtro aplicado: {linhas_antes} → {linhas_depois} linhas (removidas {linhas_antes - linhas_depois} linhas com 'Não')")
        else:
            print("⚠️ Coluna 'executante_sim' não encontrada, pulando filtro")
        
        # 6. Limpar dados nulos e converter tipos
        print("🔄 Limpando dados e convertendo tipos...")
        
        # Converter id_legalone para int8
        if 'id_legalone' in df_processed.columns:
            df_processed['id_legalone'] = pd.to_numeric(df_processed['id_legalone'], errors='coerce').astype('Int64')
        
        # Converter campos numéricos para string (text no Supabase)
        text_columns = ['pasta_proc', 'numero_cnj', 'executante', 'executante_sim', 'descricao', 'link', 'status']
        for col in text_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].astype(str)
                print(f"✅ Campo '{col}' convertido para string")
        
        # Converter campos de data
        date_columns = ['inicio_data', 'conclusao_prevista_data', 'conclusao_efetiva_data', 'prazo_fatal_data']
        for col in date_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.date
        
        # Converter campos de hora
        time_columns = ['inicio_hora', 'conclusao_prevista_hora']
        for col in time_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.time
        
        print(f"✅ Processamento concluído. Linhas processadas: {len(df_processed)}")
        print("📊 Colunas finais:")
        print(df_processed.columns.tolist())
        
        return df_processed
        
    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
        return None

def extract_date_from_datetime(datetime_str):
    """
    Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss ou dd/mm/aaaa hh:mm
    Tenta primeiro com segundos, depois sem segundos
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Tenta primeiro com segundos (formato padrão)
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            # Se falhar, tenta sem segundos (formato prazo_fatal)
            dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.date()
    except:
        return None

def extract_time_from_datetime(datetime_str):
    """
    Extrai a hora de uma string no formato dd/mm/aaaa hh:mm:ss
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Converte string para datetime
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.time()
    except:
        return None

def generate_link(id_legalone):
    """
    Gera o link concatenado baseado no id_legalone
    """
    if pd.isna(id_legalone):
        return None
    
    base_url = "https://robertomatos.novajus.com.br/agenda/compromissos/DetailsCompromissoTarefa/"
    params = "?hasNavigation=True&currentPage=1&returnUrl=%2Fagenda%2FCompromissoTarefa%2FSearch"
    
    return f"{base_url}{id_legalone}{params}"

def insert_data_to_supabase_psycopg2(df, table_name):
    """
    Insere os dados usando psycopg2 (mais estável para Supabase)
    """
    print("🔗 Conectando ao Supabase via psycopg2...")
    
    # Variáveis individuais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    host = os.getenv("host") or os.getenv("SUPABASE_HOST")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    
    print(f"🔍 DEBUG - Variáveis carregadas:")
    print(f"  user: {user}")
    print(f"  password: {'*' * len(password) if password else 'NÃO DEFINIDO'}")
    print(f"  host: {host}")
    print(f"  port: {port}")
    print(f"  dbname: {dbname}")
    
    if not all([user, password, host, dbname]):
        print("❌ ERRO: Variáveis do Supabase incompletas!")
        return False
    
    try:
        # Conectar usando psycopg2
        print("🔄 Conectando com psycopg2...")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname,
            sslmode="require"
        )
        print("✅ Conexão estabelecida com sucesso!")
        
        # Teste de conectividade
        cursor = conn.cursor()
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()
        print(f"📊 Data/hora atual: {result[0]}")
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print(f"❌ ERRO: Tabela '{table_name}' não existe!")
            return False
        
        print(f"✅ Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"📊 Registros existentes: {count_before}")
        
        # Inserir dados
        columns_df = df.columns.tolist()
        columns_sql = ", ".join(f'"{col}"' for col in columns_df)
        placeholders = ", ".join(["%s"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        print(f"📊 Inserindo {len(df)} registros...")
        
        # Inserir em lotes
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            print(f"📦 Lote {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
            
            for index, row in batch_df.iterrows():
                values = tuple(row.values)
                # Converter NaN para None
                cleaned_values = tuple(None if pd.isna(v) else v for v in values)
                cursor.execute(insert_query, cleaned_values)
                total_inserted += 1
        
        # Commit das alterações
        conn.commit()
        
        # Verificar resultado
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        print(f"✅ Inserção concluída! Total inserido: {total_inserted}")
        print(f"📊 Registros: {count_before} → {count_after}")
        
        cursor.close()
        conn.close()
        print("🔌 Conexão fechada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        
        if "could not translate host name" in str(e):
            print("🌐 Erro DNS - verifique se o host está correto")
        elif "authentication failed" in str(e):
            print("🔐 Erro de autenticação - verifique usuário e senha")
        elif "SSL" in str(e):
            print("🔒 Erro SSL - verifique se sslmode='require' está sendo usado")
        
        return False

async def insert_data_to_supabase_connection_string(df, table_name):
    """
    Atualiza/Insere dados usando connection string com lógica UPSERT
    """
    print("🔗 Conectando ao Supabase via connection string...")
    
    # Connection string completa
    database_url = os.getenv("DATABASE_URL")
    
    print(f"🔍 DEBUG - Verificando connection string:")
    print(f"  DATABASE_URL: {'*' * len(database_url) if database_url else 'NÃO DEFINIDO'}")
    
    if not database_url:
        print("❌ ERRO: DATABASE_URL não configurada!")
        print("🔧 Configure DATABASE_URL no formato:")
        print("   postgresql://postgres:<SENHA>@db.<PROJECT>.supabase.co:5432/postgres?sslmode=require")
        return False
    
    try:
        # Conectar usando connection string
        print("🔄 Conectando com connection string...")
        conn = await asyncpg.connect(database_url)
        print("✅ Conexão estabelecida com sucesso!")
        
        # Teste de conectividade
        version = await conn.fetchval("SELECT version()")
        print(f"📊 Versão do PostgreSQL: {version[:50]}...")
        
        # Verificar se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"❌ ERRO: Tabela '{table_name}' não existe!")
            return False
        
        print(f"✅ Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"📊 Registros existentes: {count_before}")
        
        # Preparar dados para UPSERT
        columns_df = df.columns.tolist()
        updated_count = 0
        inserted_count = 0
        
        print(f"📊 Processando {len(df)} registros com UPSERT...")
        
        async with conn.transaction():
            for index, row in df.iterrows():
                id_legalone = row.get('id_legalone')
                if not id_legalone:
                    print(f"⚠️ Linha {index}: id_legalone não encontrado, pulando...")
                    continue
                
                # Verificar se o registro já existe
                existing_record = await conn.fetchrow(f"""
                    SELECT id_legalone FROM {table_name} WHERE id_legalone = $1
                """, id_legalone)
                
                if existing_record:
                    # ATUALIZAR registro existente
                    set_clauses = []
                    values = []
                    
                    for col in columns_df:
                        if col != 'id_legalone':  # Não incluir id_legalone no SET
                            set_clauses.append(f"{col} = ${len(values) + 1}")
                            values.append(None if pd.isna(row[col]) else row[col])
                    
                    values.append(id_legalone)  # Adicionar id_legalone para WHERE
                    
                    update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id_legalone = ${len(values)}"
                    await conn.execute(update_query, *values)
                    updated_count += 1
                else:
                    # INSERIR novo registro
                    columns_sql = ", ".join(f'"{col}"' for col in columns_df)
                    placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
                    insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
                    
                    values = tuple(row.values)
                    cleaned_values = tuple(None if pd.isna(v) else v for v in values)
                    await conn.execute(insert_query, *cleaned_values)
                    inserted_count += 1
        
        # Verificar resultado
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"✅ UPSERT concluído! {updated_count} atualizados, {inserted_count} inseridos")
        print(f"📊 Registros: {count_before} → {count_after}")
        
        try:
            await asyncio.wait_for(conn.close(), timeout=5.0)
            print("🔌 Conexão fechada com sucesso!")
        except asyncio.TimeoutError:
            print("⚠️ Timeout ao fechar conexão - forçando fechamento")
            try:
                conn.terminate()
                print("🔌 Conexão forçada a fechar com sucesso!")
            except Exception as e:
                print(f"⚠️ Erro ao forçar fechamento: {e}")
        except Exception as e:
            print(f"⚠️ Erro ao fechar conexão: {e}")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        
        if "SSL" in str(e):
            print("🔒 Erro SSL - verifique se sslmode=require está na URL")
        elif "authentication" in str(e).lower():
            print("🔐 Erro de autenticação - verifique usuário e senha")
        elif "connection" in str(e).lower():
            print("🌐 Erro de conexão - verifique a URL")
        
        return False

async def insert_data_to_supabase_api(df, table_name):
    """
    Insere os dados de um DataFrame do pandas em uma tabela do Supabase usando a API REST.
    (Não usado no fluxo principal; banco atual = apenas Hostinger.)
    """
    if create_client is None:
        print("❌ Supabase não está instalado. Use apenas Hostinger.")
        return False
    print("🔗 Conectando ao Supabase via API...")
    
    # Credenciais da API do Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"🔍 DEBUG - Verificando credenciais da API:")
    print(f"  SUPABASE_URL: {supabase_url if supabase_url else 'NÃO DEFINIDO'}")
    print(f"  SUPABASE_ANON_KEY: {'*' * len(supabase_key) if supabase_key else 'NÃO DEFINIDO'}")
    
    if not supabase_url or not supabase_key:
        print("❌ ERRO: Credenciais da API do Supabase não configuradas!")
        print("🔧 Você precisa configurar SUPABASE_URL e SUPABASE_ANON_KEY")
        print("🔧 Essas credenciais estão disponíveis no painel do Supabase em Settings > API")
        return False
    
    try:
        # Criar cliente Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Cliente Supabase criado com sucesso!")
        
        # Converter DataFrame para lista de dicionários
        data_to_insert = df.to_dict('records')
        print(f"📊 Preparando para inserir {len(data_to_insert)} registros via API...")
        
        # Inserir dados em lotes para evitar timeout
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i+batch_size]
            print(f"📦 Processando lote {i//batch_size + 1}/{(len(data_to_insert)-1)//batch_size + 1} ({len(batch)} registros)")
            
            try:
                # Inserir lote via API
                result = supabase.table(table_name).insert(batch).execute()
                
                if result.data:
                    total_inserted += len(result.data)
                    print(f"✅ Lote {i//batch_size + 1} inserido com sucesso!")
                else:
                    print(f"⚠️ Lote {i//batch_size + 1} inserido, mas sem dados retornados")
                    
            except Exception as e:
                print(f"❌ Erro ao inserir lote {i//batch_size + 1}: {e}")
                # Continuar com os próximos lotes mesmo se um falhar
                continue
        
        print(f"✅ Inserção via API concluída! Total de registros inseridos: {total_inserted}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com a API do Supabase: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        return False

async def insert_data_to_supabase(df, table_name):
    """
    Atualiza/Insere dados no Supabase com lógica UPSERT
    """
    # Credenciais do Supabase com fallback (como no Novajus)
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "**PDS2025@@")

    print(f"🔗 Conectando ao Supabase: {host}:{port}/{database}")
    print(f"👤 Usuário: {user}")
    print(f"🔐 Senha: {'*' * len(password) if password else 'NÃO CONFIGURADO'}")
    
    # Debug: Verificar se as variáveis estão sendo carregadas
    print("🔍 DEBUG - Verificando variáveis de ambiente:")
    print(f"  SUPABASE_HOST: {os.getenv('SUPABASE_HOST', 'NÃO DEFINIDO')}")
    print(f"  SUPABASE_PORT: {os.getenv('SUPABASE_PORT', 'NÃO DEFINIDO')}")
    print(f"  SUPABASE_DATABASE: {os.getenv('SUPABASE_DATABASE', 'NÃO DEFINIDO')}")
    print(f"  SUPABASE_USER: {os.getenv('SUPABASE_USER', 'NÃO DEFINIDO')}")
    print(f"  SUPABASE_PASSWORD: {'*' * len(os.getenv('SUPABASE_PASSWORD', '')) if os.getenv('SUPABASE_PASSWORD') else 'NÃO DEFINIDO'}")
    
    # Verificar se todas as credenciais estão presentes
    if not all([host, port, database, user, password]):
        print("❌ ERRO: Credenciais do Supabase incompletas!")
        print("Verifique se todos os secrets estão configurados no GitHub Actions")
        return False

    # Configurações de retry
    max_retries = 5  # Aumentado de 3 para 5
    retry_delay = 10  # Aumentado de 5 para 10 segundos
    
    for attempt in range(max_retries):
        conn = None
        try:
            print(f"🔄 Tentativa {attempt + 1}/{max_retries} - Conectando ao Supabase...")
            
            # Configurações de conexão otimizadas para pgbouncer
            conn = await asyncpg.connect(
                user=user, 
                password=password,
                host=host, 
                port=int(port), 
                database=database,
                command_timeout=30,  # Reduzido para 30 segundos
                statement_cache_size=0,  # 🔑 CRÍTICO: Desabilita prepared statements para pgbouncer
                server_settings={
                    'application_name': 'rpa_agenda_rmb',
                    'tcp_keepalives_idle': '60',
                    'tcp_keepalives_interval': '10',
                    'tcp_keepalives_count': '3',
                    'statement_timeout': '60000',  # 1 minuto
                    'idle_in_transaction_session_timeout': '60000'
                }
            )
            print("✅ Conexão com o Supabase estabelecida com sucesso!")
            
            # Teste de conectividade básica
            version = await conn.fetchval("SELECT version()")
            print(f"📊 Versão do PostgreSQL: {version[:50]}...")
            
            break
            
        except Exception as e:
            print(f"❌ Erro na tentativa {attempt + 1}: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            
            # Logs mais detalhados para diferentes tipos de erro
            if "timeout" in str(e).lower():
                print("⏰ Erro de timeout - pode ser problema de rede ou servidor lento")
            elif "authentication" in str(e).lower() or "password" in str(e).lower():
                print("🔐 Erro de autenticação - verifique usuário e senha")
            elif "connection" in str(e).lower():
                print("🌐 Erro de conexão - verifique host e porta")
            elif "database" in str(e).lower():
                print("🗄️ Erro de database - verifique se o database existe")
            
            if conn:
                try:
                    await asyncio.wait_for(conn.close(), timeout=5.0)
                except asyncio.TimeoutError:
                    try:
                        conn.terminate()
                    except:
                        pass
                except:
                    pass
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay} segundos antes da próxima tentativa...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30)  # Backoff exponencial limitado a 30s
            else:
                print(f"❌ Falha após {max_retries} tentativas. Pulando inserção no Supabase.")
                print("🔧 Possíveis soluções:")
                print("  1. Verifique se os secrets estão configurados corretamente")
                print("  2. Verifique se o Supabase está acessível")
                print("  3. Verifique se as credenciais estão corretas")
                return False

    # Se chegou aqui, a conexão foi estabelecida com sucesso
    try:
        # Teste adicional de conectividade
        print("🔍 Testando conectividade com a tabela...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"❌ ERRO: Tabela '{table_name}' não existe no Supabase!")
            print("🔧 Verifique se a tabela foi criada corretamente")
            return False
        
        print(f"✅ Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"📊 Registros existentes na tabela: {count_before}")
        
        # Preparar dados para UPSERT
        columns_df = df.columns.tolist()
        updated_count = 0
        inserted_count = 0
        
        print(f"📊 Processando {len(df)} registros com UPSERT...")
        
        async with conn.transaction():
            for index, row in df.iterrows():
                id_legalone = row.get('id_legalone')
                if not id_legalone:
                    print(f"⚠️ Linha {index}: id_legalone não encontrado, pulando...")
                    continue
                
                # Verificar se o registro já existe
                existing_record = await conn.fetchrow(f"""
                    SELECT id_legalone FROM {table_name} WHERE id_legalone = $1
                """, id_legalone)
                
                if existing_record:
                    # ATUALIZAR registro existente
                    set_clauses = []
                    values = []
                    
                    for col in columns_df:
                        if col != 'id_legalone':  # Não incluir id_legalone no SET
                            set_clauses.append(f"{col} = ${len(values) + 1}")
                            values.append(None if pd.isna(row[col]) else row[col])
                    
                    values.append(id_legalone)  # Adicionar id_legalone para WHERE
                    
                    update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id_legalone = ${len(values)}"
                    await conn.execute(update_query, *values)
                    updated_count += 1
                else:
                    # INSERIR novo registro
                    columns_sql = ", ".join(f'"{col}"' for col in columns_df)
                    placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
                    insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
                    
                    values = tuple(row.values)
                    cleaned_values = []
                    for v in values:
                        if pd.isna(v) or str(v) == 'NaT':
                            cleaned_values.append(None)
                        else:
                            cleaned_values.append(v)
                    cleaned_values = tuple(cleaned_values)
                    await conn.execute(insert_query, *cleaned_values)
                    inserted_count += 1
        
        # Verificar resultado
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"✅ UPSERT concluído! {updated_count} atualizados, {inserted_count} inseridos")
        print(f"📊 Registros na tabela antes: {count_before}, depois: {count_after}")
        
        return True

    except Exception as e:
        print(f"❌ Erro ao processar dados no Supabase: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        print(f"🔍 Detalhes do erro: {str(e)}")
        return False
    finally:
        if conn:
            try:
                await asyncio.wait_for(conn.close(), timeout=5.0)
                print("🔌 Conexão com o Supabase fechada.")
            except asyncio.TimeoutError:
                print("⚠️ Timeout ao fechar conexão - forçando fechamento")
                try:
                    conn.terminate()
                    print("🔌 Conexão forçada a fechar com sucesso!")
                except Exception as e:
                    print(f"⚠️ Erro ao forçar fechamento: {e}")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão: {e}")

def update_data_to_supabase_psycopg2(df, table_name):
    """
    Atualiza/Insere dados no Supabase usando psycopg2 com lógica UPSERT
    Usa id_legalone como chave para UPDATE/INSERT
    """
    print(f"🔄 Atualizando/Inserindo dados na tabela {table_name} via psycopg2 (UPSERT)...")
    
    # Credenciais do Supabase
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "L7CEsmTv@vZKfpN")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Preparar dados para UPSERT
        columns = list(df.columns)
        updated_rows = 0
        inserted_rows = 0
        
        # Processar cada linha usando UPSERT
        for index, row in df.iterrows():
            id_legalone = row.get('id_legalone')
            if not id_legalone:
                print(f"⚠️ Linha {index}: id_legalone não encontrado, pulando...")
                continue
            
            # Verificar se o registro já existe
            check_query = f"SELECT id_legalone FROM {table_name} WHERE id_legalone = %s"
            cursor.execute(check_query, (id_legalone,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # ATUALIZAR registro existente
                set_clauses = []
                values = []
                
                for col in columns:
                    if col != 'id_legalone':  # Não incluir id_legalone no SET
                        set_clauses.append(f"{col} = %s")
                        values.append(row[col])
                
                values.append(id_legalone)  # Adicionar id_legalone para WHERE
                
                update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id_legalone = %s"
                cursor.execute(update_query, values)
                updated_rows += 1
                print(f"✅ Registro {id_legalone} atualizado")
            else:
                # INSERIR novo registro
                columns_sql = ", ".join(f'"{col}"' for col in columns)
                placeholders = ", ".join(["%s"] * len(columns))
                insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
                
                values = tuple(row.values)
                cursor.execute(insert_query, values)
                inserted_rows += 1
                print(f"✅ Registro {id_legalone} inserido")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ UPSERT concluído! {updated_rows} atualizados, {inserted_rows} inseridos na tabela {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar dados via psycopg2: {e}")
        return False

async def run():
    async with async_playwright() as p:
        # Configuração automática do modo headless
        # Detecta se está em ambiente sem interface gráfica (GitHub Actions, etc.)
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        
        # Se estiver em ambiente CI/CD (GitHub Actions), força headless
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            headless_mode = True
            
        print(f"Executando em modo {'headless' if headless_mode else 'com interface gráfica'}")
        browser = await p.chromium.launch(headless=headless_mode)
        
        chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" 
        context = await browser.new_context(user_agent=chrome_user_agent)
        
        page = await context.new_page()

        # --- CREDENCIAIS DE LOGIN NO SISTEMA NOVAJUS ---
        USERNAME = os.getenv("NOVAJUS_USERNAME", "rpa.icscore@ics-core.com")
        PASSWORD = os.getenv("NOVAJUS_PASSWORD", "Pds2025@@")

        # --- ETAPA 1: NAVEGAR PARA A PÁGINA DE LOGIN ---
        novajus_login_url = "https://login.novajus.com.br/conta/login" 
        print(f"Navegando para {novajus_login_url}...")
        
        try:
            await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=60000) 
            print(f"DEBUG: URL atual após page.goto(): {page.url}")
            await page.screenshot(path="debug_initial_page.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_initial_page.png' tirada após page.goto().")
        except TimeoutError:
            print(f"Erro FATAL: page.goto() para {novajus_login_url} excedeu o tempo limite. Verifique sua conexão ou a URL.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para a página de login: {e}")
            await browser.close()
            return

        # --- LÓGICA PARA CLICAR NO BOTÃO ONEPASS (SE PRESENTE) ---
        onepass_selector = '#btn-login-onepass' 
        print(f"Verificando e clicando no botão OnePass '{onepass_selector}' se presente...")
        try:
            onepass_button = page.locator(onepass_selector)
            if await onepass_button.is_visible(timeout=5000): 
                print("Botão OnePass detectado. Clicando...")
                await onepass_button.click()
                await page.wait_for_load_state("domcontentloaded") 
                await page.wait_for_timeout(1000) # Pequena pausa
                print("Clicou em OnePass. Aguardando a tela de login principal.")
                await page.screenshot(path="debug_after_onepass_click.png", full_page=True)
            else:
                print("Botão OnePass não visível. Prosseguindo.")
        except TimeoutError:
            print("Botão OnePass não encontrado no tempo esperado. Assumindo que já está na tela principal.")
        except Exception as e:
            print(f"Erro ao lidar com o botão OnePass: {e}")

        # --- ETAPA 2: INSERIR E-MAIL ---
        print("Aguardando o campo de e-mail '#Username' aparecer e ficar visível...")
        try:
            await page.wait_for_selector('#Username', state='visible', timeout=30000)
            print(f"Preenchendo e-mail: {USERNAME}...")
            await page.fill('#Username', USERNAME)
            
            await page.keyboard.press('Tab') 
            print("Pressionado TAB após preencher o e-mail. Aguardando a tela de senha mudar...")
            
            await page.wait_for_selector('#password', state='visible', timeout=30000) 
            print("Nova tela de senha com ID '#password' detectada.")
            await page.screenshot(path="debug_after_username_fill.png", full_page=True)
            
        except TimeoutError:
            print("Erro FATAL: Campo de e-mail '#Username' ou transição para senha não ocorreu no tempo esperado.")
            await page.screenshot(path="debug_username_or_transition_error.png", full_page=True)
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher e-mail e aguardar transição: {e}")
            await page.screenshot(path="debug_username_fill_error.png", full_page=True)
            await browser.close()
            return

        # --- ETAPA 3: INSERIR SENHA E CLICAR NO BOTÃO FINAL DE LOGIN ---
        print("Preenchendo senha no campo '#password'...")
        try:
            await page.fill('#password', PASSWORD)
            print("Senha preenchida.")

            login_button_selector = 'button._button-login-password'
            print(f"Clicando no botão 'Entrar' final '{login_button_selector}'...")
            await page.wait_for_selector(login_button_selector, state='visible', timeout=30000)
            await page.click(login_button_selector)
            print("Botão 'Entrar' final clicado.")

            print("Aguardando o carregamento completo da página após o login (networkidle)...")
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            await page.screenshot(path="debug_after_final_login_click.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_after_final_login_click.png' tirada após o login.")
            print(f"DEBUG: URL atual após login: {page.url}")

        except TimeoutError:
            print("Erro FATAL: Campo de senha '#password' ou botão de login final não apareceu/clicável no tempo esperado OU a página após o login não carregou totalmente.")
            await page.screenshot(path="debug_password_field_or_final_button_missing.png", full_page=True)
            print("Navegador mantido aberto para inspeção. Verifique a URL e o conteúdo da página.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher senha ou clicar no botão final: {e}")
            await page.screenshot(path="debug_password_fill_or_final_click_error.png", full_page=True)
            print("Navegador mantido aberto para inspeção. Verifique a URL e o conteúdo da página.")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 4: AGUARDAR HOME (conta rpa.icscore@ics-core.com vai direto para a home, sem tela de licença) ---
        print("Aguardando a página inicial do sistema carregar...")
        await page.wait_for_load_state("networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        print(f"📍 URL atual após login completo: {page.url}")
        await page.screenshot(path="debug_post_login_page.png", full_page=True)
        print("📸 Screenshot da página pós-login salvo: debug_post_login_page.png")

        await close_any_known_popup(page)

        # --- ETAPA 6: NAVEGAR PARA O RELATÓRIO ---
        report_url = "https://robertomatos.novajus.com.br/agenda/GenericReport/?id=674"
        print(f"Navegando para o relatório: {report_url}...")
        try:
            await page.goto(report_url, wait_until="domcontentloaded", timeout=60000)
            print(f"📍 URL atual após navegar para o relatório: {page.url}")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="debug_report_page_loaded.png", full_page=True)
            print("📸 Screenshot da página do relatório salvo: debug_report_page_loaded.png")
        except TimeoutError:
            print(f"❌ Erro: Página do relatório não carregou no tempo esperado.")
            await page.screenshot(path="debug_report_page_load_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_report_page_load_error.png")
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao navegar para o relatório: {e}")
            await page.screenshot(path="debug_report_page_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_report_page_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 7: CLICAR NO BOTÃO GERAR ---
        print("Testando o botão 'Gerar' do relatório...")
        try:
            generate_button_selector = 'button[name="ButtonSave"][type="submit"]'
            print(f"🎯 Seletor do botão: {generate_button_selector}")
            print("Aguardando o botão 'Gerar' aparecer...")
            
            # Aguarda o botão estar visível
            await page.wait_for_selector(generate_button_selector, state='visible', timeout=30000)
            
            # Tira screenshot antes de clicar
            await page.screenshot(path="debug_before_generate_click.png", full_page=True)
            print("📸 Screenshot antes de clicar no botão 'Gerar' salvo: debug_before_generate_click.png")
            
            # Clica no botão Gerar
            await page.click(generate_button_selector)
            print("✅ Botão 'Gerar' clicado com sucesso!")
            
            # Aguarda um pouco para ver o resultado
            await page.wait_for_timeout(3000)
            
            # Tira screenshot após clicar
            await page.screenshot(path="debug_after_generate_click.png", full_page=True)
            print("📸 Screenshot após clicar no botão 'Gerar' salvo: debug_after_generate_click.png")
            
            # --- AGUARDAR GERAÇÃO DO RELATÓRIO ---
            print("⏳ Aguardando a geração do relatório ser concluída...")
            print("🔄 Isso pode levar alguns minutos...")
            
            # Aguarda um tempo maior para a geração
            await page.wait_for_timeout(10000)  # 10 segundos inicial
            
            # Aguarda a página estabilizar (networkidle)
            try:
                await page.wait_for_load_state("networkidle", timeout=120000)  # 2 minutos
                print("✅ Página estabilizada após geração do relatório.")
            except TimeoutError:
                print("⚠️ Timeout aguardando estabilização da página, mas continuando...")
            
            # Aguarda mais um tempo para garantir que o relatório foi gerado
            await page.wait_for_timeout(5000)  # 5 segundos adicionais
            
            # Tira screenshot após aguardar a geração
            await page.screenshot(path="debug_after_report_generation.png", full_page=True)
            print("📸 Screenshot após aguardar geração salvo: debug_after_report_generation.png")
            print("✅ Aguardou a geração do relatório ser concluída.")
            
        except TimeoutError:
            print(f"❌ Erro: Botão 'Gerar' não encontrado.")
            await page.screenshot(path="debug_generate_button_not_found.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_generate_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao clicar no botão 'Gerar': {e}")
            await page.screenshot(path="debug_generate_button_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_generate_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 8: AGUARDAR RELATÓRIO APARECER E BAIXAR ---
        print("⏳ Aguardando o relatório ser gerado e aparecer na página atual...")
        print("🔄 Procurando pelo link 'Download' do relatório...")
        
        download_link_selector = 'a:has-text("Download")' 
        
        max_attempts = 20  # Mais tentativas já que aguardamos na mesma página
        file_path = None
        
        for i in range(max_attempts):
            try:
                print(f"🔄 Tentativa {i+1}/{max_attempts} - Procurando link 'Download'...")
                
                # Aguarda o link de download aparecer
                download_link = page.locator(download_link_selector).first
                await download_link.wait_for(state='visible', timeout=10000)
                
                if await download_link.is_enabled():
                    print(f"✅ Link 'Download' encontrado e clicável após {i+1} tentativas!")
                    
                    # Tira screenshot antes de baixar
                    await page.screenshot(path="debug_before_download.png", full_page=True)
                    print("📸 Screenshot antes do download salvo: debug_before_download.png")
                    
                    # Baixa o arquivo
                    async with page.expect_download() as download_info:
                        await download_link.click()
                        print("✅ Link 'Download' clicado.")
                    
                    download = await download_info.value
                    file_path = os.path.join(downloads_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    print(f"✅ Relatório baixado com sucesso: {file_path}")
                    break
                else:
                    print(f"⏳ Link 'Download' visível, mas não habilitado. Aguardando...")
                    await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                    
            except TimeoutError:
                print(f"⏳ Link 'Download' não visível na tentativa {i+1}/{max_attempts}. Aguardando...")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
            except Exception as e:
                print(f"❌ Erro inesperado na tentativa {i+1}/{max_attempts}: {e}")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
        else:
            print(f"❌ Erro: Link 'Download' não apareceu após {max_attempts} tentativas.")
            await page.screenshot(path="debug_download_link_not_available.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_download_link_not_available.png")
            await browser.close()
            return

        # --- ETAPA 9: PROCESSAR ARQUIVO E INSERIR NO MYSQL HOSTINGER ---
        print("\n" + "="*70)
        print("🔄 PROCESSANDO ARQUIVO BAIXADO E ATUALIZANDO NO MYSQL HOSTINGER")
        print("="*70)
        
        if file_path:
            print(f"📁 Arquivo baixado: {file_path}")
            
            df_processed = await process_excel_file(file_path)
            
            if df_processed is not None and not df_processed.empty:
                print("🔄 Inserindo/atualizando dados no MySQL Hostinger...")
                success = False
                try:
                    result = upsert_agenda_base_hostinger(df_processed, "agenda_base", "id_legalone")
                    if result:
                        success = True
                        if isinstance(result, tuple) and len(result) == 4:
                            _, inseridos, atualizados, pulados = result
                            total = inseridos + atualizados
                            print("")
                            print("="*70)
                            print(f"RESUMO: {total} itens processados (inseridos: {inseridos}, atualizados: {atualizados}, pulados: {pulados})")
                            print("="*70)
                        print("✅ Dados atualizados no MySQL Hostinger com sucesso!")
                    else:
                        print("⚠️ Falha ao atualizar dados no MySQL Hostinger.")
                except Exception as e:
                    print(f"❌ Erro ao atualizar MySQL Hostinger: {e}")
                
                if success:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"🗑️ Arquivo baixado removido: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Erro ao remover arquivo {file_path}: {e}")
                else:
                    print("💾 Salvando dados localmente como backup...")
                    backup_file = f"backup_atualiza_cumpridos_parecer_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    backup_path = os.path.join(downloads_dir, backup_file)
                    df_processed.to_excel(backup_path, index=False)
                    print(f"📁 Backup salvo em: {backup_path}")
            else:
                print("❌ Arquivo vazio ou erro no processamento.")
        else:
            print("❌ Nenhum arquivo foi baixado.")

        print("\n" + "="*70)
        print("🎯 SCRIPT CONCLUÍDO APÓS DOWNLOAD DO RELATÓRIO")
        print("="*70)
        print("✅ Processo completo realizado com sucesso!")
        print(f"📍 URL atual: {page.url}")
        if file_path:
            print(f"📁 Arquivo baixado: {file_path}")
        print("="*70)
        
        await browser.close()
        return

        # --- CÓDIGO REMOVIDO TEMPORARIAMENTE PARA INSPEÇÃO ---
        # Todo o código após o login foi removido para permitir inspeção
        # Será restaurado após identificar as alterações necessárias

# --- NOVA FUNÇÃO PARA TESTAR APENAS A INSERÇÃO NO SUPABASE ---
async def test_supabase_insertion():
    print("\n--- INICIANDO TESTE DE INSERÇÃO NO SUPABASE ---")

    # --- ATENÇÃO: Defina o caminho completo para o arquivo Excel/CSV existente ---
    # Exemplo: 'downloads/1. Relatório diário de publicações (51).xlsx'
    # CERTIFIQUE-SE DE QUE ESTE ARQUIVO EXISTE NA SUA PASTA 'downloads'!
    existing_file_name = "1. Relatório diário de publicações (51).xlsx" # <--- AJUSTE O NOME DO SEU ARQUIVO AQUI
    file_path = os.path.join(downloads_dir, existing_file_name)

    if not os.path.exists(file_path):
        print(f"ERRO: Arquivo '{file_path}' não encontrado. Por favor, verifique o nome do arquivo ou se ele está na pasta 'downloads'.")
        return

    # 1. Ler o arquivo Excel/CSV
    df_report = read_excel_file(file_path)

    if df_report is not None and not df_report.empty:
        # 1.1. Renomear colunas do DataFrame para corresponder ao Supabase
        print("Realizando mapeamento e renomeação de colunas...")
        column_mapping = {
            'Pasta': 'lo_pasta',
            'Número de CNJ': 'lo_numerocnj',
            'Número antigo': 'lo_numeroantigo', # <- Tratamento para esta coluna
            'Outro número': 'lo_outronumero',   # <- Tratamento para esta coluna
            'Cliente principal': 'lo_cliente',
            'Contrário principal': 'lo_contrario',
            'Ação': 'lo_acao',
            'Data da publicação': 'data_publicacao', 
            'Andamentos / Tipo': 'lo_tipoandamento',
            'Teor da publicação': 'lo_descricao',
            'Id': 'lo_idpubli',
        }
        df_report = df_report.rename(columns=column_mapping, errors='ignore') 
        print("Colunas renomeadas. Novas colunas do DataFrame:")
        print(df_report.columns.tolist())

        # --- TRATAMENTO: Converter colunas para string ---
        columns_to_convert_to_str = ['lo_numeroantigo', 'lo_outronumero']
        for col_name in columns_to_convert_to_str:
            if col_name in df_report.columns:
                print(f"Convertendo coluna '{col_name}' para string...")
                # Preenche valores NaN com uma string vazia antes de converter para str
                df_report[col_name] = df_report[col_name].fillna('').astype(str)
                print(f"Coluna '{col_name}' convertida. Novo tipo: {df_report[col_name].dtype}")
            else:
                print(f"Aviso: Coluna '{col_name}' não encontrada no DataFrame para conversão.")
        # --- FIM DO TRATAMENTO ---

        # 1.2. Adicionar nova coluna com valor fixo
        print("Adicionando coluna 'origem_dados' com valor fixo 'LegalOne'...")
        df_report['origem_dados'] = 'LegalOne' 
        print("Coluna 'origem_dados' adicionada. Colunas finais do DataFrame:")
        print(df_report.columns.tolist())

        # 2. Inserir no Supabase
        supabase_table_name = "agenda_base"
        success = await insert_data_to_supabase(df_report, supabase_table_name)
        if success:
            print("Processamento e inserção no Supabase concluídos!")
        else:
            print("Falha no processamento e inserção no Supabase.")
    elif df_report is not None and df_report.empty:
        print("O arquivo de teste está vazio, nada para inserir no Supabase.")
    else:
        print("Não foi possível ler o arquivo de teste, pulando a inserção no Supabase.")

    print("--- TESTE DE INSERÇÃO NO SUPABASE CONCLUÍDO ---")


# --- Execução principal do script ---
if __name__ == "__main__":
    # Para rodar o teste de inserção no Supabase:
    # asyncio.run(test_supabase_insertion())

    # Para rodar a automação COMPLETA (descomente a linha abaixo e comente a de cima):
    asyncio.run(run())
