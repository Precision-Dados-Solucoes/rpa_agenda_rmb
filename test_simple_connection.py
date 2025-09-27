#!/usr/bin/env python3
"""
Script simples para testar conexão com Supabase
Focado apenas em diagnosticar problemas de conectividade
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def test_simple_connection():
    """Teste simples de conexão"""
    print("="*60)
    print("🧪 TESTE SIMPLES DE CONEXÃO SUPABASE")
    print("="*60)
    
    # Teste 1: Connection String
    print("\n1️⃣ TESTANDO CONNECTION STRING...")
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL não encontrada!")
        return False
    
    print(f"📡 URL: {database_url[:50]}...")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Connection String: SUCESSO!")
        
        # Teste básico
        result = await conn.fetchval("SELECT 1")
        print(f"📊 Teste básico: {result}")
        
        await conn.close()
        print("🔌 Conexão fechada")
        
    except Exception as e:
        print(f"❌ Connection String: FALHOU - {e}")
        return False
    
    # Teste 2: Conexão Direta
    print("\n2️⃣ TESTANDO CONEXÃO DIRETA...")
    
    host = os.getenv("SUPABASE_HOST")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER")
    password = os.getenv("SUPABASE_PASSWORD")
    
    if not all([host, user, password]):
        print("❌ Credenciais diretas incompletas!")
        return False
    
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            ssl='require'
        )
        print("✅ Conexão Direta: SUCESSO!")
        
        # Teste básico
        result = await conn.fetchval("SELECT 1")
        print(f"📊 Teste básico: {result}")
        
        await conn.close()
        print("🔌 Conexão fechada")
        
    except Exception as e:
        print(f"❌ Conexão Direta: FALHOU - {e}")
        return False
    
    print("\n✅ AMBOS OS TESTES PASSARAM!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_simple_connection())
    
    print("\n" + "="*60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Supabase está acessível")
        print("✅ Credenciais estão corretas")
        print("🚀 Pronto para usar no RPA!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique as credenciais e conectividade")
    print("="*60)
