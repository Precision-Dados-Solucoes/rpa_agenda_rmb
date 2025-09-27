#!/usr/bin/env python3
"""
Script de debug para mostrar exatamente os dados de conexão
Ajuda a identificar problemas nas credenciais ou conectividade
"""

import os
from dotenv import load_dotenv
import socket
import ssl

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def debug_connection_data():
    """Mostra todos os dados de conexão para debug"""
    print("="*80)
    print("🔍 DEBUG COMPLETO DOS DADOS DE CONEXÃO")
    print("="*80)
    
    # 1. Verificar variáveis de ambiente
    print("\n1️⃣ VARIÁVEIS DE AMBIENTE CARREGADAS:")
    print("-" * 50)
    
    # Variáveis individuais
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    dbname = os.getenv("dbname")
    
    # Variáveis SUPABASE_*
    supabase_user = os.getenv("SUPABASE_USER")
    supabase_password = os.getenv("SUPABASE_PASSWORD")
    supabase_host = os.getenv("SUPABASE_HOST")
    supabase_port = os.getenv("SUPABASE_PORT")
    supabase_database = os.getenv("SUPABASE_DATABASE")
    
    # DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    print("📋 VARIÁVEIS INDIVIDUAIS:")
    print(f"  user: {user}")
    print(f"  password: {'*' * len(password) if password else 'NÃO DEFINIDO'}")
    print(f"  host: {host}")
    print(f"  port: {port}")
    print(f"  dbname: {dbname}")
    
    print("\n📋 VARIÁVEIS SUPABASE_*:")
    print(f"  SUPABASE_USER: {supabase_user}")
    print(f"  SUPABASE_PASSWORD: {'*' * len(supabase_password) if supabase_password else 'NÃO DEFINIDO'}")
    print(f"  SUPABASE_HOST: {supabase_host}")
    print(f"  SUPABASE_PORT: {supabase_port}")
    print(f"  SUPABASE_DATABASE: {supabase_database}")
    
    print("\n📋 DATABASE_URL:")
    print(f"  DATABASE_URL: {database_url[:50] + '...' if database_url and len(database_url) > 50 else database_url}")
    
    # 2. Verificar se todas as variáveis estão presentes
    print("\n2️⃣ VERIFICAÇÃO DE COMPLETUDE:")
    print("-" * 50)
    
    # Usar variáveis individuais ou SUPABASE_* como fallback
    final_user = user or supabase_user
    final_password = password or supabase_password
    final_host = host or supabase_host
    final_port = port or supabase_port or "5432"
    final_dbname = dbname or supabase_database
    
    print(f"✅ Usuário final: {final_user}")
    print(f"✅ Senha final: {'*' * len(final_password) if final_password else 'NÃO DEFINIDO'}")
    print(f"✅ Host final: {final_host}")
    print(f"✅ Porta final: {final_port}")
    print(f"✅ Database final: {final_dbname}")
    
    # Verificar se todas estão presentes
    missing_vars = []
    if not final_user:
        missing_vars.append("user/SUPABASE_USER")
    if not final_password:
        missing_vars.append("password/SUPABASE_PASSWORD")
    if not final_host:
        missing_vars.append("host/SUPABASE_HOST")
    if not final_dbname:
        missing_vars.append("dbname/SUPABASE_DATABASE")
    
    if missing_vars:
        print(f"\n❌ VARIÁVEIS FALTANDO: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ TODAS AS VARIÁVEIS ESTÃO PRESENTES!")
    
    # 3. Teste de conectividade de rede
    print("\n3️⃣ TESTE DE CONECTIVIDADE DE REDE:")
    print("-" * 50)
    
    try:
        print(f"🔄 Testando resolução DNS para {final_host}...")
        ip_address = socket.gethostbyname(final_host)
        print(f"✅ DNS resolvido: {final_host} → {ip_address}")
        
        print(f"🔄 Testando conectividade TCP na porta {final_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 segundos de timeout
        result = sock.connect_ex((final_host, int(final_port)))
        sock.close()
        
        if result == 0:
            print(f"✅ Porta {final_port} está acessível!")
        else:
            print(f"❌ Porta {final_port} não está acessível (código: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"❌ Erro DNS: {e}")
        print("🔧 Verifique se o host está correto")
        return False
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False
    
    # 4. Teste de SSL
    print("\n4️⃣ TESTE DE SSL:")
    print("-" * 50)
    
    try:
        print(f"🔄 Testando SSL para {final_host}:{final_port}...")
        context = ssl.create_default_context()
        with socket.create_connection((final_host, int(final_port)), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=final_host) as ssock:
                print(f"✅ SSL funcionando! Certificado: {ssock.getpeercert()['subject']}")
    except Exception as e:
        print(f"❌ Erro SSL: {e}")
        print("🔧 SSL pode estar com problemas, mas pode funcionar com sslmode=require")
    
    # 5. Resumo dos dados que serão usados
    print("\n5️⃣ RESUMO DOS DADOS PARA CONEXÃO:")
    print("-" * 50)
    print("🔗 DADOS QUE SERÃO USADOS NA CONEXÃO:")
    print(f"  Host: {final_host}")
    print(f"  Porta: {final_port}")
    print(f"  Usuário: {final_user}")
    print(f"  Senha: {'*' * len(final_password)}")
    print(f"  Database: {final_dbname}")
    print(f"  SSL Mode: require")
    
    # 6. URL de conexão que seria usada
    print("\n6️⃣ URL DE CONEXÃO GERADA:")
    print("-" * 50)
    connection_url = f"postgresql://{final_user}:{final_password}@{final_host}:{final_port}/{final_dbname}?sslmode=require"
    print(f"URL: {connection_url[:50]}...")
    print("🔧 Esta é a URL que seria usada para conectar")
    
    return True

def test_psycopg2_with_debug():
    """Testa psycopg2 com debug detalhado"""
    print("\n7️⃣ TESTE REAL COM PSYCOPG2:")
    print("-" * 50)
    
    try:
        import psycopg2
        
        # Obter dados finais
        user = os.getenv("user") or os.getenv("SUPABASE_USER")
        password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
        host = os.getenv("host") or os.getenv("SUPABASE_HOST")
        port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
        dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
        
        print(f"🔄 Tentando conectar com psycopg2...")
        print(f"   Host: {host}")
        print(f"   Porta: {port}")
        print(f"   Usuário: {user}")
        print(f"   Database: {dbname}")
        
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname,
            sslmode="require"
        )
        
        print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
        
        # Teste básico
        cursor = conn.cursor()
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()
        print(f"📊 Data/hora atual: {result[0]}")
        
        cursor.close()
        conn.close()
        print("🔒 Conexão fechada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO NA CONEXÃO: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        
        # Análise detalhada do erro
        error_str = str(e).lower()
        if "could not translate host name" in error_str:
            print("🌐 PROBLEMA: DNS não consegue resolver o host")
            print("🔧 SOLUÇÃO: Verifique se o host está correto")
        elif "authentication failed" in error_str:
            print("🔐 PROBLEMA: Falha na autenticação")
            print("🔧 SOLUÇÃO: Verifique usuário e senha")
        elif "connection refused" in error_str:
            print("🚫 PROBLEMA: Conexão recusada")
            print("🔧 SOLUÇÃO: Verifique se o Supabase está acessível")
        elif "ssl" in error_str:
            print("🔒 PROBLEMA: Erro de SSL")
            print("🔧 SOLUÇÃO: Verifique se sslmode=require está sendo usado")
        elif "timeout" in error_str:
            print("⏰ PROBLEMA: Timeout de conexão")
            print("🔧 SOLUÇÃO: Verifique conectividade de rede")
        
        return False

if __name__ == "__main__":
    print("🔍 DEBUG COMPLETO DE CONEXÃO SUPABASE")
    print("=" * 80)
    
    # Debug dos dados
    data_ok = debug_connection_data()
    
    if data_ok:
        # Teste real
        connection_ok = test_psycopg2_with_debug()
        
        print("\n" + "="*80)
        if connection_ok:
            print("🎉 DEBUG CONCLUÍDO: CONEXÃO FUNCIONANDO!")
            print("✅ Todos os dados estão corretos")
            print("✅ Conectividade OK")
            print("✅ SSL funcionando")
            print("🚀 Pronto para usar no RPA!")
        else:
            print("❌ DEBUG CONCLUÍDO: PROBLEMA IDENTIFICADO!")
            print("🔧 Verifique os erros acima para corrigir")
    else:
        print("\n" + "="*80)
        print("❌ DEBUG CONCLUÍDO: DADOS INCOMPLETOS!")
        print("🔧 Configure as variáveis de ambiente primeiro")
    
    print("="*80)
