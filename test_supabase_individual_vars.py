#!/usr/bin/env python3
"""
Script para testar conexão usando variáveis individuais (como sugerido pelo Supabase)
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def test_individual_variables():
    """Teste usando variáveis individuais como sugerido pelo Supabase"""
    print("="*70)
    print("🧪 TESTE COM VARIÁVEIS INDIVIDUAIS (SUGESTÃO SUPABASE)")
    print("="*70)
    
    # Obter variáveis individuais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    host = os.getenv("host") or os.getenv("SUPABASE_HOST")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    
    print("🔍 VARIÁVEIS CARREGADAS:")
    print(f"  user: {user}")
    print(f"  password: {'*' * len(password) if password else 'NÃO DEFINIDO'}")
    print(f"  host: {host}")
    print(f"  port: {port}")
    print(f"  dbname: {dbname}")
    
    if not all([user, password, host, dbname]):
        print("❌ Variáveis incompletas!")
        return False
    
    try:
        print("\n🔄 Conectando com variáveis individuais...")
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=dbname,
            ssl='require'  # SSL obrigatório para Supabase
        )
        print("✅ Conexão estabelecida com sucesso!")
        
        # Teste básico
        result = await conn.fetchval("SELECT NOW()")
        print(f"📊 Data/hora atual: {result}")
        
        # Teste de versão
        version = await conn.fetchval("SELECT version()")
        print(f"📊 PostgreSQL: {version[:50]}...")
        
        # Verificar tabela
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'agenda_base'
            )
        """)
        
        if table_exists:
            print("✅ Tabela 'agenda_base' encontrada!")
            count = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
            print(f"📊 Registros na tabela: {count}")
        else:
            print("⚠️ Tabela 'agenda_base' não encontrada")
        
        await conn.close()
        print("🔌 Conexão fechada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        
        if "SSL" in str(e):
            print("🔒 Erro SSL - verifique se ssl='require' está sendo usado")
        elif "authentication" in str(e).lower():
            print("🔐 Erro de autenticação - verifique usuário e senha")
        elif "connection" in str(e).lower():
            print("🌐 Erro de conexão - verifique host e porta")
        elif "Name or service not known" in str(e):
            print("🌐 Erro DNS - verifique se o host está correto")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_individual_variables())
    
    print("\n" + "="*70)
    if success:
        print("🎉 TESTE COM VARIÁVEIS INDIVIDUAIS: SUCESSO!")
        print("✅ Conexão funcionando com variáveis individuais")
        print("✅ SSL configurado corretamente")
        print("🚀 Esta abordagem funciona melhor!")
    else:
        print("❌ TESTE COM VARIÁVEIS INDIVIDUAIS: FALHOU!")
        print("🔧 Verifique as variáveis individuais")
        print("🔧 Certifique-se que todos os secrets estão configurados")
    print("="*70)
