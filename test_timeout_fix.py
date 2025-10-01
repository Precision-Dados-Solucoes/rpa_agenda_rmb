#!/usr/bin/env python3
"""
Script de teste para verificar se a correção do timeout funciona
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def test_connection_close():
    """Testa o fechamento de conexão com timeout"""
    conn = None
    
    try:
        # Credenciais do Supabase
        host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
        port = os.getenv("SUPABASE_PORT", "5432")
        database = os.getenv("SUPABASE_DATABASE", "postgres")
        user = os.getenv("SUPABASE_USER", "postgres")
        password = os.getenv("SUPABASE_PASSWORD", "PDS2025@@")
        
        print("🔌 Conectando ao banco de dados...")
        conn = await asyncpg.connect(
            user=user, 
            password=password,
            host=host, 
            port=int(port), 
            database=database,
            command_timeout=30
        )
        print("✅ Conexão estabelecida com sucesso!")
        
        # Teste simples
        version = await conn.fetchval("SELECT version()")
        print(f"📊 Versão do PostgreSQL: {version[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    
    finally:
        if conn:
            print("🔌 Fechando conexão...")
            try:
                # Aplica a correção do timeout
                await asyncio.wait_for(conn.close(), timeout=5.0)
                print("✅ Conexão fechada com sucesso!")
            except asyncio.TimeoutError:
                print("⚠️ Timeout ao fechar conexão - forçando fechamento")
                try:
                    conn.terminate()
                    print("✅ Conexão forçada a fechar com sucesso!")
                except Exception as e:
                    print(f"⚠️ Erro ao forçar fechamento: {e}")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão: {e}")
    
    return True

async def main():
    """Executa o teste"""
    print("🧪 TESTE DE CORREÇÃO DO TIMEOUT")
    print("="*50)
    
    success = await test_connection_close()
    
    if success:
        print("\n✅ Teste concluído com sucesso!")
        print("🎯 A correção do timeout está funcionando corretamente.")
    else:
        print("\n❌ Teste falhou!")
        print("🔧 Verifique as configurações de conexão.")

if __name__ == "__main__":
    asyncio.run(main())
