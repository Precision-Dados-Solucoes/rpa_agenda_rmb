"""
Módulo auxiliar para operações no Azure SQL Database
Funções reutilizáveis para inserir/atualizar dados em diferentes tabelas
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

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
        print("\n[AZURE] [ERRO] Configuracoes incompletas no config.env!")
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
        print(f"\n[AZURE] [ERRO] Nenhum driver ODBC para SQL Server encontrado!")
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
        return conn
    except Exception as e:
        print(f"\n[AZURE] [ERRO] Erro ao conectar ao Azure SQL Database: {e}")
        return None

def upsert_agenda_base(df, table_name="agenda_base", primary_key="id_legalone"):
    """
    Faz UPSERT na tabela agenda_base
    UPDATE se existe, INSERT se não existe (baseado em id_legalone)
    """
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
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
        
        # Filtrar apenas colunas que existem no DataFrame
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        if primary_key not in columns_df:
            print(f"[AZURE] [ERRO] Chave primaria '{primary_key}' nao encontrada no DataFrame")
            return False
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Preparar queries
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        # Processar cada registro
        for index, row in df.iterrows():
            id_value = row.get(primary_key)
            if not id_value or pd.isna(id_value):
                skipped_count += 1
                continue
            
            # Verificar se existe
            check_query = f"SELECT {primary_key} FROM {table_name} WHERE {primary_key} = ?"
            cursor.execute(check_query, (id_value,))
            exists = cursor.fetchone()
            
            if exists:
                # UPDATE
                set_clauses = []
                values = []
                for col in columns_df:
                    if col != primary_key:
                        set_clauses.append(f"[{col}] = ?")
                        values.append(None if pd.isna(row[col]) else row[col])
                values.append(id_value)  # Para WHERE
                
                update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {primary_key} = ?"
                cursor.execute(update_query, values)
                updated_count += 1
            else:
                # INSERT
                values = []
                for col in columns_df:
                    value = row[col]
                    values.append(None if pd.isna(value) else value)
                
                cursor.execute(insert_query, values)
                inserted_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[AZURE] [OK] {table_name}: Inseridos={inserted_count}, Atualizados={updated_count}, Pulados={skipped_count}")
        return True
        
    except Exception as e:
        print(f"[AZURE] [ERRO] Erro ao fazer UPSERT em {table_name}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def upsert_andamento_base(df, table_name="andamento_base", primary_key="id_andamento_legalone"):
    """
    Faz UPSERT na tabela andamento_base
    UPDATE se existe, INSERT se não existe (baseado em id_andamento_legalone)
    """
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Obter colunas da tabela
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        table_columns = [row[0] for row in cursor.fetchall()]
        
        # Filtrar apenas colunas que existem no DataFrame
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        if primary_key not in columns_df:
            print(f"[AZURE] [ERRO] Chave primaria '{primary_key}' nao encontrada no DataFrame")
            return False
        
        # Validar FK: carregar IDs válidos de agenda_base
        if 'id_agenda_legalone' in columns_df:
            cursor.execute("SELECT id_legalone FROM agenda_base")
            valid_agenda_ids = set(row[0] for row in cursor.fetchall())
            df = df[df['id_agenda_legalone'].isin(valid_agenda_ids)].copy()
            print(f"[AZURE] [INFO] Validacao FK: {len(df)} registros com id_agenda_legalone valido")
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Preparar queries
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        # Processar cada registro
        for index, row in df.iterrows():
            id_value = row.get(primary_key)
            if not id_value or pd.isna(id_value):
                skipped_count += 1
                continue
            
            # Verificar se existe
            check_query = f"SELECT {primary_key} FROM {table_name} WHERE {primary_key} = ?"
            cursor.execute(check_query, (id_value,))
            exists = cursor.fetchone()
            
            if exists:
                # UPDATE
                set_clauses = []
                values = []
                for col in columns_df:
                    if col != primary_key:
                        set_clauses.append(f"[{col}] = ?")
                        values.append(None if pd.isna(row[col]) else row[col])
                values.append(id_value)  # Para WHERE
                
                update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {primary_key} = ?"
                cursor.execute(update_query, values)
                updated_count += 1
            else:
                # INSERT
                values = []
                for col in columns_df:
                    value = row[col]
                    values.append(None if pd.isna(value) else value)
                
                cursor.execute(insert_query, values)
                inserted_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[AZURE] [OK] {table_name}: Inseridos={inserted_count}, Atualizados={updated_count}, Pulados={skipped_count}")
        return True
        
    except Exception as e:
        print(f"[AZURE] [ERRO] Erro ao fazer UPSERT em {table_name}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def insert_publicacoes(df, table_name="publicacoes"):
    """
    Insere publicações na tabela publicacoes
    Remove duplicatas baseado em numero_cnj + data_publicacao antes de inserir
    """
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Obter colunas da tabela (exceto id e created_at)
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
        
        # Remover duplicatas baseado em numero_cnj + data_publicacao
        if 'numero_cnj' in df.columns and 'data_publicacao' in df.columns:
            linhas_antes = len(df)
            df = df.drop_duplicates(subset=['numero_cnj', 'data_publicacao'], keep='last')
            if linhas_antes > len(df):
                print(f"[AZURE] [INFO] Removidas {linhas_antes - len(df)} duplicatas do DataFrame")
        
        inserted_count = 0
        skipped_count = 0
        
        # Preparar query
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        # Processar cada registro
        for index, row in df.iterrows():
            values = []
            for col in columns_df:
                value = row[col]
                values.append(None if pd.isna(value) else value)
            
            try:
                cursor.execute(insert_query, values)
                inserted_count += 1
            except Exception as e:
                # Se for erro de duplicata ou outro, pular
                skipped_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[AZURE] [OK] {table_name}: Inseridos={inserted_count}, Pulados={skipped_count}")
        return True
        
    except Exception as e:
        print(f"[AZURE] [ERRO] Erro ao inserir em {table_name}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

