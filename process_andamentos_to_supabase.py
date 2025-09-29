#!/usr/bin/env python3
"""
Processa arquivo de andamentos e insere/atualiza no Supabase
Sistema UPSERT: compara id_andamento_legalone com id_andamento do banco
"""

import asyncio
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def extract_date_from_datetime(datetime_str):
    """Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss e converte para aaaa/mm/dd"""
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        # Retorna no formato aaaa/mm/dd
        return dt.strftime('%Y/%m/%d')
    except:
        return None

async def process_andamentos_file_with_upsert(file_path):
    """
    Processa arquivo de andamentos com sistema UPSERT
    """
    print("PROCESSAMENTO DE ARQUIVO DE ANDAMENTOS COM UPSERT")
    print("="*70)
    
    # 1. Ler o arquivo Excel
    print("Lendo arquivo Excel...")
    try:
        df = pd.read_excel(file_path)
        print(f"Arquivo lido com sucesso: {len(df)} linhas")
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return False
    
    # 2. Processar dados (mesmo processamento do script original)
    print("Processando dados...")
    df_processed = await process_excel_file(file_path)
    
    if df_processed is None or df_processed.empty:
        print("Erro no processamento dos dados")
        return False
    
    print(f"Dados processados: {len(df_processed)} linhas")
    
    # 3. Conectar ao banco e fazer UPSERT
    try:
        # Conectar ao Supabase
        if not await connect_to_database():
            return False
        
        # Processar com UPSERT
        success = await process_dataframe_with_upsert(df_processed, "andamento_base")
        
        if success:
            print("Processamento com UPSERT concluido com sucesso!")
            return True
        else:
            print("Erro no processamento com UPSERT")
            return False
            
    except Exception as e:
        print(f"Erro durante processamento: {e}")
        return False
    finally:
        await close_connection()

async def process_excel_file(file_path):
    """
    Processa o arquivo Excel baixado com todos os tratamentos necessários.
    """
    print("Iniciando processamento do arquivo Excel...")
    
    # 1. Ler o arquivo
    try:
        df = pd.read_excel(file_path)
        print(f"Arquivo lido com sucesso. Linhas: {len(df)}")
        
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None
    
    try:
        # 2. Criar DataFrame processado com as colunas do Supabase
        df_processed = pd.DataFrame()
        
        # Mapeamento direto (sem tratamento)
        direct_mappings = {
            'id_agenda_legalone': 'id_agenda_legalone',
            'id_andamento_legalone': 'id_andamento_legalone',
            'tipo_andamento': 'tipo_andamento',
            'subtipo_andamento': 'subtipo_andamento',
            'descricao_andamento': 'descricao_andamento'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"Coluna '{excel_col}' -> '{supabase_col}'")
            else:
                print(f"Coluna '{excel_col}' nao encontrada no arquivo")
                df_processed[supabase_col] = None
        
        # 3. Tratamento especial para campo 'cadastro_andamento'
        print("Processando campo 'cadastro_andamento'...")
        if 'cadastro_andamento' in df.columns:
            # Aplicar transformacao: dd/mm/aaaa hh:mm:ss -> aaaa/mm/dd
            df_processed['cadastro_andamento'] = df['cadastro_andamento'].apply(extract_date_from_datetime)
            print("Campo 'cadastro_andamento' processado (dd/mm/aaaa hh:mm:ss -> aaaa/mm/dd)")
        else:
            print("Coluna 'cadastro_andamento' nao encontrada no arquivo")
            df_processed['cadastro_andamento'] = None
        
        # 4. Limpar dados e converter tipos conforme especificacao
        print("Limpando dados e convertendo tipos...")
        
        # Converter campos int8
        int8_columns = ['id_agenda_legalone', 'id_andamento_legalone']
        for col in int8_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').astype('Int64')
                print(f"Campo '{col}' convertido para int8")
        
        # Converter campos text
        text_columns = ['tipo_andamento', 'subtipo_andamento', 'descricao_andamento']
        for col in text_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].astype(str)
                print(f"Campo '{col}' convertido para text")
        
        # Converter campo date (cadastro_andamento ja esta no formato correto)
        if 'cadastro_andamento' in df_processed.columns:
            # Verificar se ha valores validos
            valid_dates = df_processed['cadastro_andamento'].notna().sum()
            print(f"Campo 'cadastro_andamento' processado: {valid_dates} datas validas")
        
        print(f"Processamento concluido. Linhas processadas: {len(df_processed)}")
        print("Colunas finais:")
        print(df_processed.columns.tolist())
        
        return df_processed
        
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        return None

# Variaveis globais para conexao
conn = None

async def connect_to_database():
    """Conecta ao banco de dados Supabase"""
    global conn
    
    # Credenciais do Supabase
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "PDS2025@@")

    print(f"Conectando ao Supabase: {host}:{port}/{database}")
    print(f"Usuario: {user}")
    
    try:
        conn = await asyncpg.connect(
            user=user, 
            password=password,
            host=host, 
            port=int(port), 
            database=database,
            command_timeout=30,
            statement_cache_size=0,  # Desabilita prepared statements para pgbouncer
            server_settings={
                'application_name': 'rpa_andamentos_rmb',
                'tcp_keepalives_idle': '60',
                'tcp_keepalives_interval': '10',
                'tcp_keepalives_count': '3',
                'statement_timeout': '60000',
                'idle_in_transaction_session_timeout': '60000'
            }
        )
        print("Conexao com o Supabase estabelecida com sucesso!")
        
        # Teste de conectividade
        version = await conn.fetchval("SELECT version()")
        print(f"Versao do PostgreSQL: {version[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"Erro na conexao: {e}")
        return False

async def process_dataframe_with_upsert(df, table_name):
    """
    Processa DataFrame com sistema UPSERT
    Compara id_andamento_legalone com id_andamento do banco
    """
    global conn
    
    try:
        print(f"Processando {len(df)} registros com UPSERT...")
        
        # Verificar se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"ERRO: Tabela '{table_name}' nao existe no Supabase!")
            return False
        
        print(f"Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"Registros existentes na tabela: {count_before}")
        
        # Processar cada registro com UPSERT
        updated_count = 0
        inserted_count = 0
        
        for index, row in df.iterrows():
            try:
                # Verificar se o registro ja existe
                existing_record = await conn.fetchrow("""
                    SELECT id_andamento FROM {} WHERE id_andamento = $1
                """.format(table_name), row['id_andamento_legalone'])
                
                if existing_record:
                    # ATUALIZAR registro existente
                    await conn.execute("""
                        UPDATE {} SET 
                            id_agenda_legalone = $1,
                            tipo_andamento = $2,
                            subtipo_andamento = $3,
                            descricao_andamento = $4,
                            cadastro_andamento = $5
                        WHERE id_andamento = $6
                    """.format(table_name), 
                        row['id_agenda_legalone'],
                        row['tipo_andamento'],
                        row['subtipo_andamento'],
                        row['descricao_andamento'],
                        row['cadastro_andamento'],
                        row['id_andamento_legalone']
                    )
                    updated_count += 1
                    print(f"Registro atualizado: id_andamento = {row['id_andamento_legalone']}")
                else:
                    # INSERIR novo registro
                    await conn.execute("""
                        INSERT INTO {} (
                            id_agenda_legalone, 
                            id_andamento, 
                            tipo_andamento, 
                            subtipo_andamento, 
                            descricao_andamento, 
                            cadastro_andamento
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """.format(table_name),
                        row['id_agenda_legalone'],
                        row['id_andamento_legalone'],
                        row['tipo_andamento'],
                        row['subtipo_andamento'],
                        row['descricao_andamento'],
                        row['cadastro_andamento']
                    )
                    inserted_count += 1
                    print(f"Registro inserido: id_andamento = {row['id_andamento_legalone']}")
                    
            except Exception as e:
                print(f"Erro ao processar registro {index}: {e}")
                continue
        
        # Verificar resultado final
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        
        print(f"\nUPSERT CONCLUIDO:")
        print(f"Registros atualizados: {updated_count}")
        print(f"Registros inseridos: {inserted_count}")
        print(f"Total processados: {updated_count + inserted_count}")
        print(f"Registros na tabela: {count_before} -> {count_after}")
        
        return True
        
    except Exception as e:
        print(f"Erro durante UPSERT: {e}")
        return False

async def close_connection():
    """Fecha a conexao com o banco"""
    global conn
    if conn:
        await conn.close()
        print("Conexao fechada com sucesso!")

async def test_upsert_with_sample_data():
    """Testa o sistema UPSERT com dados de exemplo"""
    print("TESTE DO SISTEMA UPSERT")
    print("="*50)
    
    # Criar dados de exemplo
    sample_data = {
        'id_agenda_legalone': [12345, 67890, 11111],
        'id_andamento_legalone': [1001, 1002, 1003],
        'tipo_andamento': ['Tipo A', 'Tipo B', 'Tipo C'],
        'subtipo_andamento': ['Subtipo A', 'Subtipo B', 'Subtipo C'],
        'descricao_andamento': ['Descricao A', 'Descricao B', 'Descricao C'],
        'cadastro_andamento': ['2024/01/15', '2024/01/16', '2024/01/17']
    }
    
    df_sample = pd.DataFrame(sample_data)
    print(f"Dados de exemplo criados: {len(df_sample)} registros")
    
    # Processar com UPSERT
    try:
        # Conectar ao banco
        if not await connect_to_database():
            return False
        
        # Processar com UPSERT
        success = await process_dataframe_with_upsert(df_sample, "andamento_base")
        
        if success:
            print("Teste de UPSERT concluido com sucesso!")
        else:
            print("Teste de UPSERT falhou")
        
        return success
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False
    finally:
        await close_connection()

if __name__ == "__main__":
    print("PROCESSADOR DE ANDAMENTOS COM UPSERT")
    print("Este script processa arquivos de andamentos e faz UPSERT no Supabase")
    print("Compara id_andamento_legalone com id_andamento do banco")
    print("")
    
    # Para testar com dados de exemplo:
    # asyncio.run(test_upsert_with_sample_data())
    
    # Para processar arquivo real (descomente e ajuste o caminho):
    # file_path = "downloads/z-rpa_andamentos_agenda_rmb_queeue.xlsx"
    # asyncio.run(process_andamentos_file_with_upsert(file_path))
    
    print("Script configurado. Descomente as linhas acima para executar.")
