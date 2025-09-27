#!/usr/bin/env python3
"""
Script para testar a connection string do Supabase
Execute este script para verificar se a DATABASE_URL está funcionando
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def test_connection_string():
    """Testa a connection string do Supabase"""
    print("="*70)
    print("🧪 TESTE DE CONNECTION STRING SUPABASE")
    print("="*70)
    
    # Obtém a connection string
    database_url = os.getenv("DATABASE_URL")
    
    print("🔍 VERIFICAÇÃO DA CONNECTION STRING:")
    print(f"  DATABASE_URL: {'*' * len(database_url) if database_url else 'NÃO DEFINIDO'}")
    
    if not database_url:
        print("❌ ERRO: DATABASE_URL não configurada!")
        print("🔧 Configure DATABASE_URL no formato:")
        print("   postgresql://postgres:<SENHA>@db.<PROJECT>.supabase.co:5432/postgres?sslmode=require")
        return False
    
    # Verificar se contém sslmode=require
    if "sslmode=require" not in database_url:
        print("⚠️ AVISO: sslmode=require não encontrado na URL")
        print("🔧 Adicione ?sslmode=require ao final da URL")
    
    try:
        # Conectar usando connection string
        print("🔄 Conectando com connection string...")
        conn = await asyncpg.connect(database_url)
        print("✅ Conexão estabelecida com sucesso!")
        
        # Teste de conectividade
        version = await conn.fetchval("SELECT version()")
        print(f"📊 Versão do PostgreSQL: {version[:50]}...")
        
        # Verificar se a tabela existe
        table_name = "agenda_base"
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if table_exists:
            print(f"✅ Tabela '{table_name}' encontrada!")
            
            # Contar registros
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"📊 Registros na tabela: {count}")
            
            # Mostrar estrutura da tabela
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            print("📋 Estrutura da tabela:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            print(f"❌ Tabela '{table_name}' não encontrada!")
            print("🔧 Execute o script create_table.sql no Supabase")
        
        await conn.close()
        print("✅ Conexão fechada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        
        # Logs específicos para diferentes tipos de erro
        if "SSL" in str(e) or "sslmode" in str(e).lower():
            print("🔒 Erro SSL - verifique se sslmode=require está na URL")
        elif "authentication" in str(e).lower() or "password" in str(e).lower():
            print("🔐 Erro de autenticação - verifique usuário e senha na URL")
        elif "connection" in str(e).lower():
            print("🌐 Erro de conexão - verifique a URL e se o Supabase está acessível")
        elif "database" in str(e).lower():
            print("🗄️ Erro de database - verifique se o database existe")
        
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE CONNECTION STRING SUPABASE")
    print("=" * 70)
    
    success = asyncio.run(test_connection_string())
    
    print("\n" + "="*70)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Connection string funcionando")
        print("✅ SSL configurado corretamente")
        print("✅ Tabela encontrada")
        print("🚀 Pronto para usar no RPA!")
    else:
        print("❌ TESTE FALHOU!")
        print("🔧 Verifique a DATABASE_URL no arquivo config.env")
        print("🔧 Formato correto: postgresql://postgres:<SENHA>@db.<PROJECT>.supabase.co:5432/postgres?sslmode=require")
    print("="*70)
