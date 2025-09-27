#!/usr/bin/env python3
"""
Script para testar hosts alternativos do Supabase
Tenta encontrar o host correto
"""

import psycopg2
import socket
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def test_dns_resolution():
    """Testa resolução DNS de hosts alternativos"""
    print("="*70)
    print("🔍 TESTE DE RESOLUÇÃO DNS - HOSTS ALTERNATIVOS")
    print("="*70)
    
    # Hosts alternativos para testar
    test_hosts = [
        "db.dhfmqumwizrwdbjnbcua.supabase.co",  # Host original
        "db.supabase.co",  # Host genérico
        "supabase.co",  # Host principal
        "aws-us-east-1.supabase.co",  # Host AWS
        "aws-us-west-2.supabase.co",  # Host AWS
    ]
    
    for host in test_hosts:
        print(f"\n🔄 Testando DNS para: {host}")
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ DNS resolvido: {host} → {ip}")
            
            # Testar conectividade na porta 5432
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, 5432))
            sock.close()
            
            if result == 0:
                print(f"✅ Porta 5432 acessível em {host}")
                return host
            else:
                print(f"❌ Porta 5432 não acessível em {host}")
                
        except socket.gaierror as e:
            print(f"❌ DNS falhou para {host}: {e}")
        except Exception as e:
            print(f"❌ Erro ao testar {host}: {e}")
    
    return None

def test_connection_with_host(host):
    """Testa conexão com host específico"""
    print(f"\n🧪 TESTANDO CONEXÃO COM HOST: {host}")
    print("-" * 50)
    
    # Obter credenciais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    
    try:
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname,
            sslmode="require"
        )
        print(f"✅ CONEXÃO ESTABELECIDA COM {host}!")
        
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
        print(f"❌ Erro na conexão com {host}: {e}")
        return False

def main():
    print("🔍 TESTE DE HOSTS ALTERNATIVOS SUPABASE")
    print("=" * 70)
    
    # Testar resolução DNS
    working_host = test_dns_resolution()
    
    if working_host:
        print(f"\n✅ HOST FUNCIONANDO ENCONTRADO: {working_host}")
        
        # Testar conexão real
        if test_connection_with_host(working_host):
            print(f"\n🎉 SUCESSO! Use o host: {working_host}")
            print("🔧 Atualize o secret SUPABASE_HOST no GitHub")
        else:
            print(f"\n❌ Host {working_host} resolve DNS mas falha na conexão")
            print("🔧 Verifique as credenciais")
    else:
        print("\n❌ NENHUM HOST FUNCIONANDO ENCONTRADO!")
        print("🔧 Possíveis problemas:")
        print("  1. Projeto Supabase foi deletado/pausado")
        print("  2. Host mudou completamente")
        print("  3. Problema de rede do GitHub Actions")
        print("  4. Projeto não existe mais")
        
        print("\n🔧 SOLUÇÕES:")
        print("  1. Verificar se o projeto existe no painel Supabase")
        print("  2. Criar novo projeto se necessário")
        print("  3. Obter novas credenciais")
        print("  4. Verificar se o projeto está ativo")

if __name__ == "__main__":
    main()
