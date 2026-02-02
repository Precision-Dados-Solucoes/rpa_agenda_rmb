#!/usr/bin/env python3
"""
Script para importar agenda completa no MySQL Hostinger
- Executa UPSERT na tabela agenda_base no MySQL Hostinger
- Compara id_legalone do arquivo com o banco
- Atualiza registros existentes e insere novos (colunas de data tratadas no helper)
- Arquivo: Downloads/import-new-agenda.xlsx
"""

import os
import pandas as pd
import psycopg2
import pyodbc
from dotenv import load_dotenv
from hostinger_mysql_helper import upsert_agenda_base

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def read_excel_file(file_path):
    """Lê um arquivo Excel e retorna um DataFrame do pandas."""
    print(f"📖 Lendo o arquivo: {file_path}")
    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, forneça um arquivo .xlsx ou .csv")
        
        print(f"✅ Arquivo '{file_path}' lido com sucesso.")
        print(f"📊 Total de linhas: {len(df)}")
        print(f"📋 Colunas encontradas: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo não encontrado em {file_path}")
        return None
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo Excel: {e}")
        return None

def extract_date_from_datetime(datetime_str):
    """Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss ou dd/mm/aaaa hh:mm"""
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
    """Extrai a hora de uma string no formato dd/mm/aaaa hh:mm:ss"""
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.time()
    except:
        return None

def generate_link(id_legalone):
    """Gera o link concatenado baseado no id_legalone"""
    if pd.isna(id_legalone):
        return None
    
    base_url = "https://robertomatos.novajus.com.br/agenda/compromissos/DetailsCompromissoTarefa/"
    params = "?hasNavigation=True&currentPage=1&returnUrl=%2Fagenda%2FCompromissoTarefa%2FSearch"
    
    return f"{base_url}{id_legalone}{params}"

def process_excel_file(file_path):
    """Processa o arquivo Excel com todos os tratamentos necessários."""
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
            'status': 'status',
            'cliente-processo': 'cliente-processo'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"✅ Coluna '{excel_col}' → '{supabase_col}'")
            else:
                # Tentar variações do nome da coluna (especialmente para 'cliente-processo')
                if supabase_col == 'cliente-processo':
                    possible_names = ['cliente-processo', 'Cliente-processo', 'Cliente-Processo', 
                                     'CLIENTE-PROCESSO', 'cliente_processo', 'Cliente_processo', 
                                     'Cliente_Processo', 'CLIENTE_PROCESSO']
                    found = False
                    for name in possible_names:
                        if name in df.columns:
                            df_processed[supabase_col] = df[name]
                            print(f"✅ Coluna '{name}' → '{supabase_col}'")
                            found = True
                            break
                    if not found:
                        print(f"⚠️ Coluna '{excel_col}' não encontrada no arquivo (tentou variações)")
                        df_processed[supabase_col] = None
                else:
                    print(f"⚠️ Coluna '{excel_col}' não encontrada no arquivo")
                    df_processed[supabase_col] = None
        
        # 3. Tratamento de campos de data/hora
        print("🔄 Processando campos de data/hora...")
        
        if 'inicio' in df.columns:
            df_processed['inicio_data'] = df['inicio'].apply(extract_date_from_datetime)
            df_processed['inicio_hora'] = df['inicio'].apply(extract_time_from_datetime)
            print("✅ Campo 'inicio' processado → 'inicio_data' e 'inicio_hora'")
        
        if 'conclusao_prevista' in df.columns:
            df_processed['conclusao_prevista_data'] = df['conclusao_prevista'].apply(extract_date_from_datetime)
            df_processed['conclusao_prevista_hora'] = df['conclusao_prevista'].apply(extract_time_from_datetime)
            print("✅ Campo 'conclusao_prevista' processado → 'conclusao_prevista_data' e 'conclusao_prevista_hora'")
        
        if 'conclusao_efetiva' in df.columns:
            df_processed['conclusao_efetiva_data'] = df['conclusao_efetiva'].apply(extract_date_from_datetime)
            print("✅ Campo 'conclusao_efetiva' processado → 'conclusao_efetiva_data'")
        
        if 'cadastro' in df.columns:
            df_processed['cadastro'] = df['cadastro'].apply(extract_date_from_datetime)
            print("✅ Campo 'cadastro' processado → formato aaaa/mm/dd")
        
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
        text_columns = ['pasta_proc', 'numero_cnj', 'executante', 'executante_sim', 'descricao', 'link', 'status', 'cliente-processo']
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
        import traceback
        traceback.print_exc()
        return None

def delete_all_records(table_name):
    """Deleta todos os registros da tabela agenda_base no Supabase"""
    print(f"🗑️  Deletando todos os registros da tabela '{table_name}' (Supabase)...")
    
    # Variáveis individuais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    host = os.getenv("host") or os.getenv("SUPABASE_HOST")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    
    if not all([user, password, host, dbname]):
        print("❌ ERRO: Variáveis do Supabase incompletas!")
        return False
    
    try:
        # Conectar usando psycopg2
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname,
            sslmode="require"
        )
        
        cursor = conn.cursor()
        
        # Contar registros antes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"📊 Registros existentes antes da exclusão: {count_before}")
        
        # Deletar todos os registros
        cursor.execute(f"DELETE FROM {table_name}")
        deleted_count = cursor.rowcount
        
        # Commit das alterações
        conn.commit()
        
        # Verificar resultado
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Exclusão concluída! {deleted_count} registros deletados")
        print(f"📊 Registros: {count_before} → {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao deletar registros: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_all_records_azure(table_name):
    """Deleta todos os registros da tabela agenda_base no Azure SQL Database"""
    print(f"🗑️  Deletando todos os registros da tabela '{table_name}' (Azure)...")
    
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            print("❌ ERRO: Não foi possível conectar ao Azure SQL Database!")
            return False
        
        cursor = conn.cursor()
        
        # Contar registros antes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"📊 Registros existentes antes da exclusão: {count_before}")
        
        # Deletar todos os registros
        cursor.execute(f"DELETE FROM {table_name}")
        deleted_count = cursor.rowcount
        
        # Commit das alterações
        conn.commit()
        
        # Verificar resultado
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Exclusão concluída! {deleted_count} registros deletados")
        print(f"📊 Registros: {count_before} → {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao deletar registros no Azure: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

def insert_all_data(df, table_name):
    """Insere todos os dados processados na tabela agenda_base no Supabase"""
    print(f"📤 Inserindo {len(df)} registros na tabela '{table_name}' (Supabase)...")
    
    # Variáveis individuais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    host = os.getenv("host") or os.getenv("SUPABASE_HOST")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    
    if not all([user, password, host, dbname]):
        print("❌ ERRO: Variáveis do Supabase incompletas!")
        return False
    
    try:
        # Conectar usando psycopg2
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname,
            sslmode="require"
        )
        
        cursor = conn.cursor()
        
        # Preparar dados para inserção
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
            print(f"📦 Lote {i//batch_size + 1}/{(len(df)-1)//batch_size + 1} ({len(batch_df)} registros)")
            
            for index, row in batch_df.iterrows():
                values = tuple(row.values)
                # Converter NaN para None
                cleaned_values = tuple(None if pd.isna(v) else v for v in values)
                cursor.execute(insert_query, cleaned_values)
                total_inserted += 1
            
            # Commit do lote
            conn.commit()
            print(f"✅ Lote {i//batch_size + 1} inserido com sucesso!")
        
        # Verificar resultado
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Inserção concluída! Total inserido: {total_inserted}")
        print(f"📊 Total de registros na tabela: {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_all_data_azure(df, table_name):
    """Insere todos os dados processados na tabela agenda_base no Azure SQL Database"""
    print(f"📤 Inserindo {len(df)} registros na tabela '{table_name}' (Azure)...")
    
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            print("❌ ERRO: Não foi possível conectar ao Azure SQL Database!")
            return False
        
        cursor = conn.cursor()
        
        # Obter colunas da tabela (exceto created_at que é auto)
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            AND COLUMN_NAME != 'created_at'
            ORDER BY ORDINAL_POSITION
        """)
        table_columns = [row[0] for row in cursor.fetchall()]
        
        # Filtrar apenas colunas que existem no DataFrame e na tabela
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        if not columns_df:
            print("❌ ERRO: Nenhuma coluna do DataFrame corresponde às colunas da tabela!")
            return False
        
        # Preparar dados para inserção
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        print(f"📊 Inserindo {len(df)} registros...")
        print(f"📋 Colunas a inserir: {columns_df}")
        
        # Inserir em lotes
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            print(f"📦 Lote {i//batch_size + 1}/{(len(df)-1)//batch_size + 1} ({len(batch_df)} registros)")
            
            for index, row in batch_df.iterrows():
                values = []
                for col in columns_df:
                    value = row[col]
                    values.append(None if pd.isna(value) else value)
                
                cursor.execute(insert_query, values)
                total_inserted += 1
            
            # Commit do lote
            conn.commit()
            print(f"✅ Lote {i//batch_size + 1} inserido com sucesso!")
        
        # Verificar resultado
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Inserção concluída! Total inserido: {total_inserted}")
        print(f"📊 Total de registros na tabela: {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados no Azure: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Função principal"""
    print("="*70)
    print("🚀 IMPORTAR AGENDA COMPLETA")
    print("="*70)
    
    # Tentar diferentes caminhos possíveis
    possible_paths = [
        "Downloads/import-new-agenda.xlsx",  # Pasta Downloads com maiúscula
        "downloads/import-new-agenda.xlsx",  # Pasta downloads com minúscula
        os.path.join(os.path.expanduser("~"), "Downloads", "import-new-agenda.xlsx"),  # Downloads do usuário
        "import-new-agenda.xlsx"  # Na raiz do projeto
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            print(f"✅ Arquivo encontrado em: {path}")
            break
    
    # Se não encontrou, pedir ao usuário
    if file_path is None:
        print(f"❌ Erro: Arquivo não encontrado em nenhum dos caminhos:")
        for path in possible_paths:
            print(f"   - {path}")
        print("\n💡 Por favor, verifique se o arquivo 'import-new-agenda.xlsx' existe")
        print("   ou forneça o caminho completo do arquivo.")
        return
    
    # 1. Processar arquivo Excel
    print("\n" + "="*70)
    print("📋 ETAPA 1: PROCESSAR ARQUIVO EXCEL")
    print("="*70)
    df_processed = process_excel_file(file_path)
    
    if df_processed is None or df_processed.empty:
        print("❌ Erro: Não foi possível processar o arquivo ou arquivo vazio.")
        return
    
    # 2. Executar UPSERT (MySQL Hostinger)
    print("\n" + "="*70)
    print("🔄 ETAPA 2: EXECUTAR UPSERT (MYSQL HOSTINGER)")
    print("="*70)
    print("📋 Comparando id_legalone do arquivo com o banco...")
    print("   - Registros existentes serão ATUALIZADOS")
    print("   - Registros novos serão INSERIDOS")
    print(f"📊 Total de registros a processar: {len(df_processed)}")
    
    success_hostinger = upsert_agenda_base(df_processed, "agenda_base", "id_legalone")
    
    if not success_hostinger:
        print("❌ Erro: Não foi possível executar UPSERT no MySQL Hostinger.")
        return
    
    # Conclusão
    print("\n" + "="*70)
    print("✅ PROCESSO CONCLUÍDO!")
    print("="*70)
    print(f"📊 Total de registros processados: {len(df_processed)}")
    print("🎉 A tabela agenda_base foi atualizada no MySQL Hostinger usando UPSERT!")

if __name__ == "__main__":
    main()
