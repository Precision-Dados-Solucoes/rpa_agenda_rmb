"""
Script para criar as tabelas no Azure SQL Database
Estrutura baseada no Supabase, mas com PKs diferentes:
- agenda_base: PK = id_legalone
- andamento_base: PK = id_andamento_legalone, FK = id_agenda_legalone -> agenda_base.id_legalone
- publicacoes: estrutura da tb_publicacoes
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

def table_exists(cursor, table_name):
    """Verifica se uma tabela já existe"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = ?
    """, table_name)
    return cursor.fetchone()[0] > 0

def index_exists(cursor, index_name):
    """Verifica se um índice já existe"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.indexes 
        WHERE name = ?
    """, index_name)
    return cursor.fetchone()[0] > 0

def criar_tabela_agenda_base(cursor):
    """Cria a tabela agenda_base com id_legalone como PK"""
    if table_exists(cursor, 'agenda_base'):
        print("[AVISO] Tabela agenda_base ja existe. Pulando criacao...")
        return
    
    print("[INFO] Criando tabela agenda_base...")
    
    cursor.execute("""
        CREATE TABLE agenda_base (
            id_legalone BIGINT PRIMARY KEY,
            compromisso_tarefa NVARCHAR(MAX),
            tipo NVARCHAR(MAX),
            subtipo NVARCHAR(MAX),
            etiqueta NVARCHAR(MAX),
            inicio_data DATE,
            inicio_hora TIME,
            conclusao_prevista_data DATE,
            conclusao_prevista_hora TIME,
            conclusao_efetiva_data DATE,
            prazo_fatal_data DATE,
            pasta_proc NVARCHAR(MAX),
            numero_cnj NVARCHAR(MAX),
            executante NVARCHAR(MAX),
            executante_sim NVARCHAR(MAX),
            descricao NVARCHAR(MAX),
            status NVARCHAR(MAX),
            link NVARCHAR(MAX),
            cadastro DATE,
            created_at DATETIME2 DEFAULT GETDATE()
        )
    """)
    
    # Criar índices (não podemos criar índice em NVARCHAR(MAX))
    if not index_exists(cursor, 'idx_agenda_base_created_at'):
        cursor.execute("CREATE INDEX idx_agenda_base_created_at ON agenda_base(created_at)")
    
    if not index_exists(cursor, 'idx_agenda_base_inicio_data'):
        cursor.execute("CREATE INDEX idx_agenda_base_inicio_data ON agenda_base(inicio_data)")
    
    if not index_exists(cursor, 'idx_agenda_base_prazo_fatal_data'):
        cursor.execute("CREATE INDEX idx_agenda_base_prazo_fatal_data ON agenda_base(prazo_fatal_data)")
    
    print("[OK] Tabela agenda_base criada com sucesso!")

def criar_tabela_andamento_base(cursor):
    """Cria a tabela andamento_base com id_andamento_legalone como PK e FK para agenda_base"""
    if table_exists(cursor, 'andamento_base'):
        print("[AVISO] Tabela andamento_base ja existe. Pulando criacao...")
        return
    
    print("[INFO] Criando tabela andamento_base...")
    
    cursor.execute("""
        CREATE TABLE andamento_base (
            id_andamento_legalone BIGINT PRIMARY KEY,
            id_agenda_legalone BIGINT NOT NULL,
            tipo_andamento NVARCHAR(MAX),
            subtipo_andamento NVARCHAR(MAX),
            descricao_andamento NVARCHAR(MAX),
            cadastro_andamento DATE,
            FOREIGN KEY (id_agenda_legalone) REFERENCES agenda_base(id_legalone)
        )
    """)
    
    # Criar índices
    if not index_exists(cursor, 'idx_andamento_base_id_agenda'):
        cursor.execute("CREATE INDEX idx_andamento_base_id_agenda ON andamento_base(id_agenda_legalone)")
    
    if not index_exists(cursor, 'idx_andamento_base_cadastro'):
        cursor.execute("CREATE INDEX idx_andamento_base_cadastro ON andamento_base(cadastro_andamento)")
    
    print("[OK] Tabela andamento_base criada com sucesso!")

def criar_tabela_publicacoes(cursor):
    """Cria a tabela publicacoes (baseada em tb_publicacoes)"""
    if table_exists(cursor, 'publicacoes'):
        print("[AVISO] Tabela publicacoes ja existe. Pulando criacao...")
        return
    
    print("[INFO] Criando tabela publicacoes...")
    
    cursor.execute("""
        CREATE TABLE publicacoes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            data_cadastro DATE,
            hora_cadastro TIME,
            data_publicacao DATE,
            hora_publicacao TIME,
            pasta NVARCHAR(MAX),
            numero_cnj NVARCHAR(MAX),
            tratamento NVARCHAR(MAX),
            publicacao NVARCHAR(MAX),
            created_at DATETIME2 DEFAULT GETDATE()
        )
    """)
    
    # Criar índices
    if not index_exists(cursor, 'idx_publicacoes_data_cadastro'):
        cursor.execute("CREATE INDEX idx_publicacoes_data_cadastro ON publicacoes(data_cadastro)")
    
    if not index_exists(cursor, 'idx_publicacoes_data_publicacao'):
        cursor.execute("CREATE INDEX idx_publicacoes_data_publicacao ON publicacoes(data_publicacao)")
    
    if not index_exists(cursor, 'idx_publicacoes_created_at'):
        cursor.execute("CREATE INDEX idx_publicacoes_created_at ON publicacoes(created_at)")
    
    print("[OK] Tabela publicacoes criada com sucesso!")

def main():
    """Função principal"""
    print("=" * 80)
    print("[CRIAR] CRIAR TABELAS NO AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Conectar ao Azure
    conn = get_azure_connection()
    if not conn:
        print("\n[ERRO] Nao foi possivel conectar ao Azure SQL Database.")
        return
    
    try:
        cursor = conn.cursor()
        
        # Criar todas as tabelas
        print("\n" + "=" * 80)
        print("[CRIANDO] CRIANDO TABELAS")
        print("=" * 80 + "\n")
        
        # 1. Criar agenda_base primeiro (pois andamento_base tem FK para ela)
        criar_tabela_agenda_base(cursor)
        
        # 2. Criar andamento_base (com FK para agenda_base)
        criar_tabela_andamento_base(cursor)
        
        # 3. Criar publicacoes
        criar_tabela_publicacoes(cursor)
        
        # Commit das alterações
        conn.commit()
        
        print("\n" + "=" * 80)
        print("[OK] PROCESSO CONCLUIDO COM SUCESSO!")
        print("=" * 80)
        print("\n[TABELAS] Tabelas criadas:")
        print("  [OK] agenda_base (PK: id_legalone)")
        print("  [OK] andamento_base (PK: id_andamento_legalone, FK: id_agenda_legalone)")
        print("  [OK] publicacoes (PK: id)")
        print("\n[INFO] Estrutura:")
        print("  - agenda_base: id_legalone como PRIMARY KEY")
        print("  - andamento_base: id_andamento_legalone como PRIMARY KEY")
        print("  - andamento_base: FOREIGN KEY (id_agenda_legalone) -> agenda_base(id_legalone)")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante a criacao das tabelas: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()
        print("\n[CONEXAO] Conexao fechada.")

if __name__ == "__main__":
    main()


