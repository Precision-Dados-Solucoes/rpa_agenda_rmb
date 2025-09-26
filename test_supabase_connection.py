#!/usr/bin/env python3
"""
Script para testar a conexão com o Supabase
Execute este script para verificar se as credenciais estão corretas
"""

import asyncio
import asyncpg
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def test_supabase_connection():
    """Testa a conexão com o Supabase"""
    print("🔄 Testando conexão com o Supabase...")
    
    # Obtém as credenciais
    host = os.getenv("SUPABASE_HOST")
    port = os.getenv("SUPABASE_PORT")
    database = os.getenv("SUPABASE_DATABASE")
    user = os.getenv("SUPABASE_USER")
    password = os.getenv("SUPABASE_PASSWORD")
    
    print(f"📡 Host: {host}")
    print(f"📡 Port: {port}")
    print(f"📡 Database: {database}")
    print(f"📡 User: {user}")
    print(f"📡 Password: {'*' * len(password) if password else 'NÃO CONFIGURADO'}")
    
    if not all([host, port, database, user, password]):
        print("❌ Erro: Credenciais do Supabase não configuradas!")
        print("Verifique o arquivo config.env")
        return False
    
    try:
        # Tenta conectar
        print("🔄 Conectando ao Supabase...")
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database
        )
        
        print("✅ Conexão estabelecida com sucesso!")
        
        # Testa uma query simples
        result = await conn.fetchval("SELECT version()")
        print(f"📊 Versão do PostgreSQL: {result}")
        
        # Verifica se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'agenda_base'
            )
        """)
        
        if table_exists:
            print("✅ Tabela 'agenda_base' existe!")
            
            # Conta registros na tabela
            count = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
            print(f"📊 Registros na tabela: {count}")
            
            # Mostra estrutura da tabela
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agenda_base'
                ORDER BY ordinal_position
            """)
            print("📋 Estrutura da tabela:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            print("⚠️ Tabela 'agenda_base' não existe!")
            print("Verifique o nome da tabela no Supabase")
        
        await conn.close()
        print("✅ Conexão fechada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com o Supabase: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTE DE CONEXÃO COM SUPABASE")
    print("="*60)
    
    success = asyncio.run(test_supabase_connection())
    
    print("="*60)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Credenciais corretas")
        print("✅ Conexão funcionando")
        print("🚀 Pronto para executar o RPA!")
    else:
        print("❌ TESTE FALHOU!")
        print("🔧 Verifique as credenciais no arquivo config.env")
        print("🔧 Execute o script create_table.sql no Supabase")
    print("="*60)
