"""
Script para importar publicações do arquivo Excel para a tabela publicacoes no Azure SQL Database
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('config.env')

def get_azure_connection():
    """
    Conecta ao Azure SQL Database
    """
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    if not server or not database or not username or not password:
        print("\n[ERRO] Configuracoes incompletas no config.env!")
        return None
    
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
        "SQL Server Native Client 11.0"
    ]
    
    available_drivers = pyodbc.drivers()
    
    driver = None
    for drv in drivers_to_try:
        if drv in available_drivers:
            driver = drv
            break
    
    if not driver:
        print(f"\n[ERRO] Nenhum driver ODBC para SQL Server encontrado!")
        return None
    
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(connection_string, timeout=30)
        print(f"[OK] Conectado ao Azure SQL Database: {server}:{port}/{database}")
        return conn
    except Exception as e:
        print(f"\n[ERRO] Erro ao conectar ao Azure SQL Database: {e}")
        return None

def processar_dataframe_publicacoes(df):
    """
    Processa o DataFrame de publicações, separando data/hora e tratando tipos de dados
    """
    print("\n[INFO] Processando DataFrame...")
    
    # Mapear colunas (case insensitive)
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'data' in col_lower and 'cadastro' in col_lower:
            col_mapping[col] = 'data_cadastro_temp'
        elif 'hora' in col_lower and 'cadastro' in col_lower:
            col_mapping[col] = 'hora_cadastro_temp'
        elif 'data' in col_lower and 'publicacao' in col_lower or ('data' in col_lower and 'hora' in col_lower and 'publicacao' in col_lower):
            col_mapping[col] = 'data_publicacao_temp'
        elif 'hora' in col_lower and 'publicacao' in col_lower:
            col_mapping[col] = 'hora_publicacao_temp'
        elif 'pasta' in col_lower:
            col_mapping[col] = 'pasta'
        elif 'cnj' in col_lower or 'numero' in col_lower:
            col_mapping[col] = 'numero_cnj'
        elif 'tratamento' in col_lower:
            col_mapping[col] = 'tratamento'
        elif 'publicacao' in col_lower:
            col_mapping[col] = 'publicacao'
    
    # Renomear colunas
    df_renamed = df.rename(columns=col_mapping)
    
    # Processar data/hora cadastro
    if 'data_cadastro_temp' in df_renamed.columns:
        df_renamed['data_cadastro'] = pd.to_datetime(df_renamed['data_cadastro_temp'], errors='coerce').dt.date
        df_renamed['hora_cadastro'] = pd.to_datetime(df_renamed['data_cadastro_temp'], errors='coerce').dt.time
        df_renamed = df_renamed.drop(columns=['data_cadastro_temp'])
    elif 'hora_cadastro_temp' in df_renamed.columns:
        # Se só tem hora, data pode estar em outra coluna
        df_renamed['hora_cadastro'] = pd.to_datetime(df_renamed['hora_cadastro_temp'], errors='coerce').dt.time
        df_renamed = df_renamed.drop(columns=['hora_cadastro_temp'])
    
    # Processar data/hora publicação
    if 'data_publicacao_temp' in df_renamed.columns:
        df_renamed['data_publicacao'] = pd.to_datetime(df_renamed['data_publicacao_temp'], errors='coerce').dt.date
        df_renamed['hora_publicacao'] = pd.to_datetime(df_renamed['data_publicacao_temp'], errors='coerce').dt.time
        df_renamed = df_renamed.drop(columns=['data_publicacao_temp'])
    elif 'hora_publicacao_temp' in df_renamed.columns:
        df_renamed['hora_publicacao'] = pd.to_datetime(df_renamed['hora_publicacao_temp'], errors='coerce').dt.time
        df_renamed = df_renamed.drop(columns=['hora_publicacao_temp'])
    
    # Garantir que as colunas existam
    required_columns = ['data_cadastro', 'hora_cadastro', 'data_publicacao', 'hora_publicacao', 
                        'pasta', 'numero_cnj', 'tratamento', 'publicacao']
    
    for col in required_columns:
        if col not in df_renamed.columns:
            df_renamed[col] = None
    
    # Converter campos de texto (substituir NaN por None)
    text_columns = ['pasta', 'numero_cnj', 'tratamento', 'publicacao']
    for col in text_columns:
        if col in df_renamed.columns:
            df_renamed[col] = df_renamed[col].replace({pd.NA: None, 'nan': None, 'None': None, '': None})
    
    # Selecionar apenas as colunas necessárias
    df_final = df_renamed[required_columns].copy()
    
    print(f"[OK] DataFrame processado: {len(df_final)} registros")
    print(f"[INFO] Colunas finais: {df_final.columns.tolist()}")
    
    return df_final

def insert_publicacoes_to_azure(df, table_name):
    """
    Insere publicações no Azure SQL Database usando UPSERT
    Como não há PK única além do id (auto-incremento), vamos usar uma combinação de campos
    ou simplesmente INSERT (sem verificação de duplicatas)
    """
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        print(f"\n{'=' * 80}")
        print(f"[UPSERT] PROCESSANDO PUBLICACOES - INSERT NO AZURE")
        print(f"{'=' * 80}")
        
        # Contar antes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"[INFO] Registros existentes: {count_before}")
        
        # Obter colunas da tabela
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            AND COLUMN_NAME != 'id'
            AND COLUMN_NAME != 'created_at'
            ORDER BY ORDINAL_POSITION
        """)
        table_columns = [row[0] for row in cursor.fetchall()]
        
        # Filtrar apenas colunas que existem no DataFrame
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        print(f"[INFO] Colunas que serao inseridas: {columns_df}")
        
        # Remover duplicatas baseado em uma combinação de campos chave
        # Usando numero_cnj + data_publicacao como chave única (se disponível)
        if 'numero_cnj' in df.columns and 'data_publicacao' in df.columns:
            print(f"[INFO] Verificando duplicatas no DataFrame...")
            linhas_antes = len(df)
            df = df.drop_duplicates(subset=['numero_cnj', 'data_publicacao'], keep='last')
            duplicatas_removidas = linhas_antes - len(df)
            if duplicatas_removidas > 0:
                print(f"[AVISO] Removidas {duplicatas_removidas} duplicatas do DataFrame")
        
        # Preparar query de INSERT
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        inserted_count = 0
        skipped_count = 0
        batch_size = 100
        total_rows = len(df)
        
        print(f"\n[INFO] Processando {total_rows} registros em lotes de {batch_size}...")
        print(f"[INFO] Usando INSERT (sem verificacao de duplicatas)...")
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            for index, row in batch_df.iterrows():
                # Preparar valores
                values = []
                for col in columns_df:
                    value = row[col]
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                
                # INSERT
                try:
                    cursor.execute(insert_query, values)
                    inserted_count += 1
                except Exception as e:
                    # Se for erro de duplicata, pular
                    if "PRIMARY KEY" in str(e) or "UNIQUE" in str(e):
                        skipped_count += 1
                    else:
                        print(f"[AVISO] Erro ao inserir registro: {str(e)[:100]}")
                        skipped_count += 1
            
            # Commit a cada lote
            conn.commit()
            
            # Mostrar progresso
            progress = (batch_end / total_rows) * 100
            print(f"[PROGRESSO] {batch_end}/{total_rows} ({progress:.1f}%) | "
                  f"Inseridos: {inserted_count} | Pulados: {skipped_count}")
        
        # Commit final
        conn.commit()
        
        # Contar após
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"\n[OK] INSERCAO CONCLUIDA!")
        print(f"   Inseridos: {inserted_count}")
        print(f"   Pulados: {skipped_count}")
        print(f"   Total na tabela: {count_before} -> {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Função principal"""
    print("=" * 80)
    print("[IMPORTAR] IMPORTAR PUBLICACOES PARA AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Buscar arquivo
    possible_paths = [
        os.path.join(os.path.expanduser("~"), "Downloads", "atualiza_publiccacao.xlsx"),
        os.path.join("downloads", "atualiza_publiccacao.xlsx"),
        os.path.join("Downloads", "atualiza_publiccacao.xlsx"),
        "atualiza_publiccacao.xlsx"
    ]
    
    file_publicacoes = None
    for path in possible_paths:
        if os.path.exists(path):
            file_publicacoes = path
            print(f"[OK] Arquivo encontrado em: {path}")
            break
    
    if not file_publicacoes:
        print(f"[ERRO] Arquivo nao encontrado: atualiza_publiccacao.xlsx")
        print(f"   Procurando em:")
        for path in possible_paths:
            print(f"   - {path}")
        return
    
    try:
        # Ler o arquivo Excel
        print(f"\n[INFO] Lendo arquivo: {file_publicacoes}")
        df_publicacoes = pd.read_excel(file_publicacoes)
        print(f"[OK] Arquivo lido: {len(df_publicacoes)} linhas")
        print(f"[INFO] Colunas encontradas: {df_publicacoes.columns.tolist()}")
        
        # Processar DataFrame
        df_processed = processar_dataframe_publicacoes(df_publicacoes)
        
        # Importar para Azure SQL Database
        success = insert_publicacoes_to_azure(df_processed, "publicacoes")
        
        if success:
            print("\n" + "=" * 80)
            print("[SUCESSO] PUBLICACOES IMPORTADAS COM SUCESSO PARA AZURE!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("[ERRO] ERRO AO IMPORTAR PUBLICACOES")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n[ERRO] Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

