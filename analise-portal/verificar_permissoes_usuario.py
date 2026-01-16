"""
Script para verificar e atualizar permissões de usuários existentes
"""
import os
import sys
import pyodbc
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ Erro: DATABASE_URL não encontrada no .env")
    sys.exit(1)

# Extrair informações da connection string
# Formato: sqlserver://usuario:senha@servidor:porta/database?encrypt=true
try:
    # Remover sqlserver://
    url = DATABASE_URL.replace('sqlserver://', '')
    
    # Separar autenticação do resto
    if '@' in url:
        auth_part, server_part = url.split('@', 1)
        user, password = auth_part.split(':')
        
        # Separar servidor e database
        if '/' in server_part:
            server_db, params = server_part.split('/', 1)
            if ':' in server_db:
                server, port = server_db.split(':')
            else:
                server = server_db
                port = '1433'
            database = params.split('?')[0]
        else:
            server = server_part.split(':')[0]
            port = '1433'
            database = 'master'
    else:
        print("❌ Formato de DATABASE_URL inválido")
        sys.exit(1)
    
    print(f"🔌 Conectando ao servidor: {server}:{port}")
    print(f"📊 Database: {database}")
    
    # Criar connection string para pyodbc
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📋 VERIFICANDO USUÁRIOS E PERMISSÕES")
    print("="*60 + "\n")
    
    # Buscar todos os usuários
    cursor.execute("""
        SELECT 
            id,
            email,
            nome,
            role,
            paginas_autorizadas,
            executantes_autorizados
        FROM Usuarios
        ORDER BY nome
    """)
    
    usuarios = cursor.fetchall()
    
    print(f"Total de usuários encontrados: {len(usuarios)}\n")
    
    usuarios_sem_permissoes = []
    
    for usuario in usuarios:
        id_user, email, nome, role, paginas, executantes = usuario
        
        print(f"👤 {nome} ({email})")
        print(f"   Role: {role}")
        print(f"   Páginas autorizadas: {paginas if paginas else 'NULL'}")
        print(f"   Executantes autorizados: {executantes if executantes else 'NULL'}")
        
        # Verificar se está NULL ou vazio
        precisa_atualizar = False
        
        if paginas is None or paginas.strip() == '':
            print("   ⚠️  Páginas autorizadas está NULL ou vazio")
            precisa_atualizar = True
        
        if executantes is None or executantes.strip() == '':
            print("   ⚠️  Executantes autorizados está NULL ou vazio")
            precisa_atualizar = True
        
        if precisa_atualizar:
            usuarios_sem_permissoes.append({
                'id': id_user,
                'email': email,
                'nome': nome,
                'role': role,
                'paginas': paginas,
                'executantes': executantes,
            })
        
        print()
    
    if usuarios_sem_permissoes:
        print("="*60)
        print(f"⚠️  {len(usuarios_sem_permissoes)} usuário(s) precisam de atualização")
        print("="*60 + "\n")
        
        resposta = input("Deseja atualizar os usuários sem permissões? (s/n): ").lower()
        
        if resposta == 's':
            for usuario in usuarios_sem_permissoes:
                print(f"\n📝 Atualizando {usuario['nome']}...")
                
                # Definir valores padrão baseado no role
                if usuario['role'] == 'administrador':
                    paginas_default = json.dumps(['dashboard_agenda', 'dashboard_indicadores', 'gerenciamento_usuarios'])
                    executantes_default = json.dumps([])  # Array vazio = todos
                else:
                    # Para não-administradores, definir valores padrão
                    # Você pode ajustar conforme necessário
                    paginas_default = json.dumps(['dashboard_agenda', 'dashboard_indicadores'])
                    executantes_default = json.dumps([])  # Array vazio = todos (pode ser alterado depois)
                
                # Atualizar apenas campos NULL ou vazios
                update_query = """
                    UPDATE Usuarios
                    SET 
                        paginas_autorizadas = CASE 
                            WHEN paginas_autorizadas IS NULL OR paginas_autorizadas = '' 
                            THEN ? 
                            ELSE paginas_autorizadas 
                        executantes_autorizados = CASE 
                            WHEN executantes_autorizados IS NULL OR executantes_autorizados = '' 
                            THEN ? 
                            ELSE executantes_autorizados 
                        END
                    WHERE id = ?
                """
                
                cursor.execute(update_query, (paginas_default, executantes_default, usuario['id']))
                conn.commit()
                
                print(f"   ✅ {usuario['nome']} atualizado com sucesso")
                print(f"      Páginas: {paginas_default}")
                print(f"      Executantes: {executantes_default}")
        else:
            print("\n❌ Atualização cancelada")
    else:
        print("="*60)
        print("✅ Todos os usuários têm permissões configuradas!")
        print("="*60)
    
    conn.close()
    print("\n✅ Verificação concluída!")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
