#!/usr/bin/env python3
"""
Script para testar conexão direta com IP
Tenta contornar problemas de DNS
"""

import psycopg2
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def test_direct_ip_connection():
    """Testa conexão direta com IP"""
    print("="*70)
    print("🧪 TESTE DE CONEXÃO DIRETA COM IP")
    print("="*70)
    
    # Obter credenciais
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    
    print(f"🔍 CREDENCIAIS:")
    print(f"  user: {user}")
    print(f"  password: {'*' * len(password) if password else 'NÃO DEFINIDO'}")
    print(f"  dbname: {dbname}")
    print(f"  port: {port}")
    
    # Lista de IPs para testar (baseado no IPv6 que apareceu)
    # Vamos tentar alguns IPs comuns do Supabase
    test_ips = [
        "54.85.79.121",  # IP comum do Supabase
        "54.85.79.122",  # IP comum do Supabase
        "54.85.79.123",  # IP comum do Supabase
        "54.85.79.124",  # IP comum do Supabase
        "54.85.79.125",  # IP comum do Supabase
    ]
    
    for ip in test_ips:
        print(f"\n🔄 Testando IP: {ip}")
        try:
            conn = psycopg2.connect(
                user=user,
                password=password,
                host=ip,
                port=port,
                dbname=dbname,
                sslmode="require"
            )
            print(f"✅ CONEXÃO ESTABELECIDA COM IP: {ip}")
            
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
            print(f"❌ IP {ip} falhou: {e}")
            continue
    
    print("\n❌ NENHUM IP FUNCIONOU!")
    return False

if __name__ == "__main__":
    success = test_direct_ip_connection()
    
    print("\n" + "="*70)
    if success:
        print("🎉 CONEXÃO COM IP DIRETO: SUCESSO!")
        print("✅ Encontramos um IP que funciona")
        print("🔧 Podemos usar este IP como solução temporária")
    else:
        print("❌ CONEXÃO COM IP DIRETO: FALHOU!")
        print("🔧 Todos os IPs testados falharam")
        print("🔧 O problema pode ser:")
        print("  1. Projeto Supabase pausado/inativo")
        print("  2. Host mudou completamente")
        print("  3. Problema de rede do GitHub Actions")
    print("="*70)
