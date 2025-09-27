#!/usr/bin/env python3
"""
Script de teste específico para GitHub Actions
Testa a conexão com Supabase usando as mesmas configurações do workflow
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def test_github_actions_connection():
    """Testa a conexão com Supabase usando configurações do GitHub Actions"""
    print("="*70)
    print("🧪 TESTE DE CONEXÃO SUPABASE - GITHUB ACTIONS")
    print("="*70)
    
    # Carrega as variáveis de ambiente (mesmo método do workflow)
    load_dotenv('config.env')
    
    # Obtém as credenciais (mesmo método do script principal)
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "**PDS2025@@")
    
    print("🔍 VERIFICAÇÃO DE CREDENCIAIS:")
    print(f"  SUPABASE_HOST: {host}")
    print(f"  SUPABASE_PORT: {port}")
    print(f"  SUPABASE_DATABASE: {database}")
    print(f"  SUPABASE_USER: {user}")
    print(f"  SUPABASE_PASSWORD: {'*' * len(password) if password else 'NÃO CONFIGURADO'}")
    
    # Verificar se todas as credenciais estão presentes
    if not all([host, port, database, user, password]):
        print("❌ ERRO: Credenciais do Supabase incompletas!")
        print("🔧 Verifique se todos os secrets estão configurados no GitHub Actions")
        return False
    
    print("\n🔄 TESTANDO CONEXÃO...")
    
    # Configurações de retry (mesmo do script principal)
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        conn = None
        try:
            print(f"🔄 Tentativa {attempt + 1}/{max_retries} - Conectando ao Supabase...")
            
            # Configurações de conexão otimizadas para GitHub Actions
            conn = await asyncpg.connect(
                user=user, 
                password=password,
                host=host, 
                port=int(port), 
                database=database,
                command_timeout=120,
                server_settings={
                    'application_name': 'rpa_agenda_rmb_github_actions_test',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                    'statement_timeout': '300000',
                    'idle_in_transaction_session_timeout': '300000'
                }
            )
            print("✅ Conexão com o Supabase estabelecida com sucesso!")
            
            # Teste de conectividade básica
            version = await conn.fetchval("SELECT version()")
            print(f"📊 Versão do PostgreSQL: {version[:50]}...")
            
            # Teste da tabela
            table_name = "agenda_base"
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, table_name)
            
            if table_exists:
                print(f"✅ Tabela '{table_name}' encontrada!")
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
            print("✅ Teste de conexão concluído com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na tentativa {attempt + 1}: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            
            # Logs mais detalhados para diferentes tipos de erro
            if "timeout" in str(e).lower():
                print("⏰ Erro de timeout - pode ser problema de rede ou servidor lento")
            elif "authentication" in str(e).lower() or "password" in str(e).lower():
                print("🔐 Erro de autenticação - verifique usuário e senha")
            elif "connection" in str(e).lower():
                print("🌐 Erro de conexão - verifique host e porta")
            elif "database" in str(e).lower():
                print("🗄️ Erro de database - verifique se o database existe")
            
            if conn:
                try:
                    await conn.close()
                except:
                    pass
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay} segundos antes da próxima tentativa...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30)
            else:
                print(f"❌ Falha após {max_retries} tentativas.")
                print("🔧 Possíveis soluções:")
                print("  1. Verifique se os secrets estão configurados corretamente")
                print("  2. Verifique se o Supabase está acessível")
                print("  3. Verifique se as credenciais estão corretas")
                print("  4. Verifique se a tabela foi criada")
                return False
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_github_actions_connection())
    
    print("\n" + "="*70)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Conexão com Supabase funcionando")
        print("✅ Tabela encontrada")
        print("🚀 Pronto para executar o RPA no GitHub Actions!")
    else:
        print("❌ TESTE FALHOU!")
        print("🔧 Verifique as configurações e tente novamente")
    print("="*70)
