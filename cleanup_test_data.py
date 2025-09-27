#!/usr/bin/env python3
"""
Script para limpar dados de teste do Supabase
"""

import asyncio
import asyncpg
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def cleanup_test_data():
    """Remove dados de teste do Supabase"""
    print("🧹 LIMPEZA DE DADOS DE TESTE")
    print("="*50)
    
    # Credenciais do Supabase
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "**PDS2025@@")
    
    print(f"🔗 Conectando ao Supabase: {host}:{port}/{database}")
    
    try:
        # Conectar
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database
        )
        print("✅ Conexão estabelecida!")
        
        # Contar registros antes da limpeza
        count_before = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
        print(f"📊 Registros antes da limpeza: {count_before}")
        
        # Remover dados de teste
        print("🗑️ Removendo dados de teste...")
        
        # Remover registro de teste específico
        deleted_test = await conn.execute("DELETE FROM agenda_base WHERE descricao = 'TESTE DE INSERÇÃO'")
        print(f"✅ Registro de teste removido: {deleted_test}")
        
        # Contar registros após limpeza
        count_after = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
        print(f"📊 Registros após limpeza: {count_after}")
        
        # Mostrar registros restantes
        if count_after > 0:
            records = await conn.fetch("SELECT id, descricao, created_at FROM agenda_base ORDER BY created_at DESC LIMIT 5")
            print("📋 Últimos registros na tabela:")
            for record in records:
                print(f"   ID: {record['id']} | Descrição: {record['descricao'][:50]}... | Criado: {record['created_at']}")
        else:
            print("📋 Tabela vazia - pronta para receber dados do RPA!")
        
        await conn.close()
        print("🔌 Conexão fechada.")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(cleanup_test_data())
    
    print("="*50)
    if success:
        print("🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("✅ Tabela pronta para receber dados do RPA amanhã!")
    else:
        print("❌ ERRO NA LIMPEZA!")
    print("="*50)

