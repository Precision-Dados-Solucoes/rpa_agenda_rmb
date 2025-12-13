"""
Script para testar conexão com Azure SQL Database
"""

import os
import pyodbc
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('config.env')

def get_available_drivers():
    """Lista os drivers ODBC disponíveis"""
    drivers = pyodbc.drivers()
    return drivers

def test_azure_connection(server=None, database=None, username=None, password=None, port=None):
    """
    Testa conexão com Azure SQL Database
    """
    print("=" * 80)
    print("[TESTE] TESTE DE CONEXAO COM AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Obter credenciais (parâmetros ou config.env)
    server = server or os.getenv("AZURE_SERVER")
    database = database or os.getenv("AZURE_DATABASE")
    username = username or os.getenv("AZURE_USER")
    password = password or os.getenv("AZURE_PASSWORD")
    port = port or os.getenv("AZURE_PORT", "1433")
    
    # Mostrar configurações (sem mostrar senha completa)
    print("[CONFIG] Configuracoes:")
    print(f"   Server: {server}")
    print(f"   Database: {database}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password) if password else '(nao configurada)'}")
    print(f"   Port: {port}")
    print()
    
    # Validar se todas as variáveis foram fornecidas
    if not all([server, database, username, password]):
        print("[ERRO] Configuracoes incompletas!")
        print("   Forneca as credenciais como parametros ou configure no config.env:")
        print("   AZURE_SERVER=seu_servidor.database.windows.net")
        print("   AZURE_DATABASE=nome_do_banco")
        print("   AZURE_USER=usuario@servidor")
        print("   AZURE_PASSWORD=senha")
        print("   AZURE_PORT=1433")
        return False
    
    # Listar drivers disponíveis
    available_drivers = get_available_drivers()
    print(f"[DRIVERS] Drivers ODBC disponiveis: {len(available_drivers)}")
    for driver in available_drivers:
        if 'SQL Server' in driver:
            print(f"   - {driver}")
    print()
    
    # Tentar diferentes drivers ODBC
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
        "SQL Server Native Client 11.0"
    ]
    
    # Encontrar um driver disponível
    driver = None
    for drv in drivers_to_try:
        if drv in available_drivers:
            driver = drv
            print(f"[OK] Usando driver: {driver}")
            break
    
    if not driver:
        print(f"[ERRO] Nenhum driver ODBC para SQL Server encontrado!")
        print(f"   Por favor, instale o 'ODBC Driver 17 for SQL Server' ou superior.")
        return False
    
    # String de conexão para Azure SQL Database
    # Azure geralmente requer Encrypt=yes e TrustServerCertificate=no
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
    
    print(f"[CONEXAO] Tentando conectar...")
    print(f"   Server: {server}:{port}")
    print(f"   Database: {database}")
    print()
    
    try:
        conn = pyodbc.connect(connection_string, timeout=30)
        print("[OK] Conexao estabelecida com sucesso!")
        print()
        
        cursor = conn.cursor()
        
        # Teste 1: Verificar versão do SQL Server
        print("[TESTE 1] Verificando versao do SQL Server...")
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"[OK] Versao: {version[:100]}...")
        print()
        
        # Teste 2: Listar bancos de dados disponíveis
        print("[TESTE 2] Listando bancos de dados...")
        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
        databases = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Bancos encontrados: {len(databases)}")
        for db in databases[:10]:  # Mostrar apenas os 10 primeiros
            print(f"   - {db}")
        if len(databases) > 10:
            print(f"   ... e mais {len(databases) - 10} bancos")
        print()
        
        # Teste 3: Listar tabelas no banco atual
        print("[TESTE 3] Listando tabelas no banco atual...")
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        tables = cursor.fetchall()
        print(f"[OK] Tabelas encontradas: {len(tables)}")
        if tables:
            for schema, table in tables[:20]:  # Mostrar apenas as 20 primeiras
                print(f"   - {schema}.{table}")
            if len(tables) > 20:
                print(f"   ... e mais {len(tables) - 20} tabelas")
        else:
            print("   (Nenhuma tabela encontrada - banco vazio)")
        print()
        
        # Teste 4: Verificar permissões
        print("[TESTE 4] Verificando permissoes...")
        cursor.execute("SELECT SYSTEM_USER, USER_NAME()")
        system_user, db_user = cursor.fetchone()
        print(f"[OK] Usuario do sistema: {system_user}")
        print(f"[OK] Usuario do banco: {db_user}")
        print()
        
        # Teste 5: Criar uma tabela de teste (se tiver permissão)
        print("[TESTE 5] Testando criacao de tabela...")
        try:
            cursor.execute("""
                IF OBJECT_ID('teste_conexao_azure', 'U') IS NOT NULL
                    DROP TABLE teste_conexao_azure
            """)
            cursor.execute("""
                CREATE TABLE teste_conexao_azure (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    teste_data DATETIME2 DEFAULT GETDATE(),
                    mensagem NVARCHAR(100)
                )
            """)
            cursor.execute("INSERT INTO teste_conexao_azure (mensagem) VALUES (?)", "Teste de conexao Azure")
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM teste_conexao_azure")
            count = cursor.fetchone()[0]
            cursor.execute("DROP TABLE teste_conexao_azure")
            conn.commit()
            print(f"[OK] Tabela de teste criada e removida com sucesso! (Registros inseridos: {count})")
        except Exception as e:
            print(f"[AVISO] Nao foi possivel criar tabela de teste: {e}")
            print("   (Isso pode ser normal se o usuario nao tiver permissoes de CREATE TABLE)")
        print()
        
        cursor.close()
        conn.close()
        
        print("=" * 80)
        print("[SUCESSO] TODOS OS TESTES PASSARAM!")
        print("=" * 80)
        print()
        print("[INFO] A conexao com Azure SQL Database esta funcionando corretamente.")
        print("   Voce pode prosseguir com a criacao das tabelas.")
        print()
        print("[DICA] Adicione as credenciais no config.env:")
        print("   AZURE_SERVER=seu_servidor.database.windows.net")
        print("   AZURE_DATABASE=nome_do_banco")
        print("   AZURE_USER=usuario@servidor")
        print("   AZURE_PASSWORD=senha")
        print("   AZURE_PORT=1433")
        
        return True
        
    except pyodbc.Error as e:
        print(f"[ERRO] Erro ao conectar ao Azure SQL Database:")
        print(f"   {str(e)}")
        print()
        print("[DICA] Verifique:")
        print("   1. Se o servidor Azure esta acessivel")
        print("   2. Se o firewall do Azure permite seu IP")
        print("   3. Se as credenciais estao corretas")
        print("   4. Se o formato do usuario esta correto (usuario@servidor)")
        print("   5. Se o firewall do Azure foi configurado para permitir seu IP")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    import sys
    
    # Se houver argumentos, usar como credenciais
    if len(sys.argv) >= 5:
        server = sys.argv[1]
        database = sys.argv[2]
        username = sys.argv[3]
        password = sys.argv[4]
        port = sys.argv[5] if len(sys.argv) > 5 else "1433"
        test_azure_connection(server, database, username, password, port)
    else:
        # Usar credenciais do config.env ou pedir ao usuário
        test_azure_connection()

if __name__ == "__main__":
    main()


