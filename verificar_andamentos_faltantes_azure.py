"""
Script para verificar detalhadamente quais andamentos estão faltando
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('config.env')

def get_azure_connection():
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    if not all([server, database, username, password]):
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
    except:
        return None

def main():
    print("=" * 80)
    print("[VERIFICAR] VERIFICACAO DETALHADA DE ANDAMENTOS FALTANTES")
    print("=" * 80)
    print()
    
    # Buscar arquivo
    file_path = os.path.join(os.path.expanduser("~"), "Downloads", "atualiza_andamentos_1212.xlsx")
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo nao encontrado: {file_path}")
        return
    
    # Conectar
    conn = get_azure_connection()
    if not conn:
        print("[ERRO] Nao foi possivel conectar ao Azure")
        return
    
    try:
        cursor = conn.cursor()
        
        # Carregar IDs da tabela
        print("[INFO] Carregando IDs da tabela andamento_base...")
        cursor.execute("SELECT id_andamento_legalone FROM andamento_base")
        existing_ids = set(row[0] for row in cursor.fetchall())
        print(f"[OK] {len(existing_ids)} IDs na tabela")
        
        # Carregar IDs válidos da agenda_base
        print("[INFO] Carregando IDs validos da agenda_base...")
        cursor.execute("SELECT id_legalone FROM agenda_base")
        valid_agenda_ids = set(row[0] for row in cursor.fetchall())
        print(f"[OK] {len(valid_agenda_ids)} IDs validos")
        
        # Ler arquivo
        print(f"\n[INFO] Lendo arquivo: {file_path}")
        df = pd.read_excel(file_path)
        print(f"[OK] {len(df)} linhas no arquivo")
        
        # Processar
        if 'id_andamento_legalone' in df.columns:
            df['id_andamento_legalone'] = pd.to_numeric(df['id_andamento_legalone'], errors='coerce').astype('Int64')
        if 'id_agenda_legalone' in df.columns:
            df['id_agenda_legalone'] = pd.to_numeric(df['id_agenda_legalone'], errors='coerce').astype('Int64')
        
        # Remover duplicatas
        df_unique = df.drop_duplicates(subset=['id_andamento_legalone'], keep='last')
        print(f"[INFO] Apos remover duplicatas: {len(df_unique)} linhas")
        
        # Filtrar: não existem na tabela
        df_nao_existem = df_unique[~df_unique['id_andamento_legalone'].isin(existing_ids)]
        print(f"[INFO] Andamentos que NAO estao na tabela: {len(df_nao_existem)}")
        
        # Separar por FK válida/inválida
        df_fk_valida = df_nao_existem[df_nao_existem['id_agenda_legalone'].isin(valid_agenda_ids)]
        df_fk_invalida = df_nao_existem[~df_nao_existem['id_agenda_legalone'].isin(valid_agenda_ids)]
        
        print(f"\n[RESUMO]")
        print(f"   - Andamentos que podem ser inseridos (FK valida): {len(df_fk_valida)}")
        print(f"   - Andamentos com FK invalida (nao podem ser inseridos): {len(df_fk_invalida)}")
        
        if len(df_fk_valida) > 0:
            print(f"\n[INFO] {len(df_fk_valida)} andamentos podem ser inseridos!")
            print(f"[INFO] Primeiros 10 id_andamento_legalone que podem ser inseridos:")
            for idx, row in df_fk_valida.head(10).iterrows():
                print(f"   - {row['id_andamento_legalone']} (agenda: {row['id_agenda_legalone']})")
        
        if len(df_fk_invalida) > 0:
            print(f"\n[INFO] {len(df_fk_invalida)} andamentos com FK invalida (id_agenda_legalone nao existe em agenda_base)")
            print(f"[INFO] Primeiros 10 id_agenda_legalone invalidos:")
            for idx, row in df_fk_invalida.head(10).iterrows():
                print(f"   - Andamento {row['id_andamento_legalone']} -> Agenda {row['id_agenda_legalone']} (nao existe)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()

