"""
Script para limpar (deletar todos os dados) da tabela andamento_base no Azure SQL Database
"""

import os
import pyodbc
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('config.env')

def get_azure_connection():
    """
    Conecta ao Azure SQL Database
    """
    # Configurações do Azure (lidas do config.env)
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    # Validar se as variáveis obrigatórias foram configuradas
    if not server or not database or not username or not password:
        print("\n[ERRO] Configuracoes incompletas no config.env!")
        print("   Configure as variaveis AZURE_*")
        return None
    
    # Tentar diferentes drivers ODBC
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
        "SQL Server Native Client 11.0"
    ]
    
    available_drivers = pyodbc.drivers()
    
    # Encontrar um driver disponível
    driver = None
    for drv in drivers_to_try:
        if drv in available_drivers:
            driver = drv
            break
    
    if not driver:
        print(f"\n[ERRO] Nenhum driver ODBC para SQL Server encontrado!")
        return None
    
    # String de conexão para Azure SQL Database
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

def limpar_andamento_base(table_name="andamento_base"):
    """
    Deleta todos os registros da tabela andamento_base
    """
    print("=" * 80)
    print("[LIMPAR] LIMPAR TABELA ANDAMENTO_BASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Conectar ao Azure
    conn = get_azure_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ?
        """, table_name)
        if cursor.fetchone()[0] == 0:
            print(f"[ERRO] Tabela '{table_name}' nao existe!")
            return False
        
        # Contar registros antes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"[INFO] Registros existentes: {count_before}")
        
        if count_before == 0:
            print("[AVISO] Tabela ja esta vazia!")
            return True
        
        # Confirmar deleção
        print(f"\n[AVISO] Voce esta prestes a deletar {count_before} registros da tabela {table_name}!")
        print("[AVISO] Esta operacao nao pode ser desfeita!")
        
        # Deletar todos os registros
        print(f"\n[INFO] Deletando todos os registros...")
        cursor.execute(f"DELETE FROM {table_name}")
        rows_deleted = cursor.rowcount
        
        # Commit
        conn.commit()
        
        # Contar após
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"\n[OK] DELECAO CONCLUIDA!")
        print(f"   Registros deletados: {rows_deleted}")
        print(f"   Total na tabela: {count_before} -> {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro durante a delecao: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    limpar_andamento_base("andamento_base")

