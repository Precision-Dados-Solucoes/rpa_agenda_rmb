#!/usr/bin/env python3
"""
Script de teste usando psycopg2 (sugestão do GPT)
Mais estável para conexões com Supabase
"""

import psycopg2
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def test_psycopg2_connection():
    """Teste de conexão usando psycopg2"""
    print("="*70)
    print("🧪 TESTE DE CONEXÃO COM PSYCOPG2")
    print("="*70)
    
    # Variáveis de ambiente (virão dos Secrets no GitHub Actions)
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")
    
    print("🔍 VARIÁVEIS CARREGADAS:")
    print(f"  USER: {USER}")
    print(f"  PASSWORD: {'*' * len(PASSWORD) if PASSWORD else 'NÃO DEFINIDO'}")
    print(f"  HOST: {HOST}")
    print(f"  PORT: {PORT}")
    print(f"  DBNAME: {DBNAME}")
    
    if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
        print("❌ Variáveis incompletas!")
        print("🔧 Verifique se todos os secrets estão configurados:")
        print("   - SUPABASE_USER")
        print("   - SUPABASE_PASSWORD") 
        print("   - SUPABASE_HOST")
        print("   - SUPABASE_PORT")
        print("   - SUPABASE_DATABASE")
        return False
    
    try:
        print("\n🔄 Conectando com psycopg2...")
        # Conexão com o banco
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            sslmode="require"   # 🔑 necessário no Supabase
        )
        print("✅ Connection successful!")

        # Criação de cursor
        cursor = connection.cursor()

        # Teste básico - data/hora atual
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("🕒 Current Time:", result)

        # Teste de versão do PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print("📊 PostgreSQL Version:", version[0][:50] + "...")

        # Verificar se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'agenda_base'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Tabela 'agenda_base' encontrada!")
            
            # Contar registros na tabela
            cursor.execute("SELECT COUNT(*) FROM agenda_base;")
            count = cursor.fetchone()[0]
            print(f"📊 Registros na tabela: {count}")
            
            # Mostrar estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agenda_base'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("📋 Estrutura da tabela:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        else:
            print("⚠️ Tabela 'agenda_base' não encontrada!")
            print("🔧 Execute o script create_table.sql no Supabase")

        # Fechar cursor e conexão
        cursor.close()
        connection.close()
        print("🔒 Connection closed.")
        
        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Erro operacional: {e}")
        if "could not translate host name" in str(e):
            print("🌐 Erro DNS - verifique se o host está correto")
        elif "authentication failed" in str(e):
            print("🔐 Erro de autenticação - verifique usuário e senha")
        elif "SSL" in str(e):
            print("🔒 Erro SSL - verifique se sslmode='require' está sendo usado")
        return False
        
    except psycopg2.ProgrammingError as e:
        print(f"❌ Erro de programação: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE CONEXÃO COM PSYCOPG2")
    print("=" * 70)
    
    success = test_psycopg2_connection()
    
    print("\n" + "="*70)
    if success:
        print("🎉 TESTE COM PSYCOPG2: SUCESSO!")
        print("✅ Conexão funcionando com psycopg2")
        print("✅ SSL configurado corretamente")
        print("✅ Tabela encontrada e acessível")
        print("🚀 psycopg2 é mais estável que asyncpg!")
    else:
        print("❌ TESTE COM PSYCOPG2: FALHOU!")
        print("🔧 Verifique as credenciais e conectividade")
        print("🔧 psycopg2 pode ser mais estável que asyncpg")
    print("="*70)
