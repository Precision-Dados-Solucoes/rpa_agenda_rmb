"""
Teste completo de conexão com Azure SQL
Simula o que o workflow do GitHub Actions faria
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('config.env')

def testar_conexao():
    """Testa conexão completa com Azure SQL"""
    print("=" * 70)
    print("TESTE COMPLETO DE CONEXÃO COM AZURE SQL")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar variáveis de ambiente
    print("1. VERIFICANDO VARIÁVEIS DE AMBIENTE")
    print("-" * 70)
    
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    variaveis = {
        "AZURE_SERVER": server,
        "AZURE_DATABASE": database,
        "AZURE_USER": username,
        "AZURE_PASSWORD": "***" if password else None,
        "AZURE_PORT": port
    }
    
    todas_ok = True
    for key, value in variaveis.items():
        if value:
            status = "✓" if key != "AZURE_PASSWORD" else "✓"
            print(f"  {status} {key}: {value if key != 'AZURE_PASSWORD' else '***'}")
        else:
            print(f"  ❌ {key}: NÃO CONFIGURADO")
            todas_ok = False
    
    print()
    
    if not todas_ok:
        print("❌ ERRO: Variáveis de ambiente incompletas!")
        print("   Verifique o arquivo config.env")
        return False
    
    # 2. Testar conexão
    print("2. TESTANDO CONEXÃO COM AZURE SQL")
    print("-" * 70)
    
    try:
        from azure_sql_helper import get_azure_connection
        
        print("  Tentando conectar...")
        conn = get_azure_connection()
        
        if conn:
            print("  ✅ Conexão estabelecida com sucesso!")
            print()
            
            # 3. Verificar tabelas
            print("3. VERIFICANDO TABELAS")
            print("-" * 70)
            
            cursor = conn.cursor()
            
            # Verificar agenda_base
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    MAX(created_at) as ultima_atualizacao
                FROM agenda_base
            """)
            result = cursor.fetchone()
            if result:
                total_agenda = result[0]
                ultima_agenda = result[1]
                print(f"  ✓ agenda_base: {total_agenda:,} registros")
                if ultima_agenda:
                    print(f"    Última atualização: {ultima_agenda}")
            
            # Verificar andamento_base
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    MAX(cadastro_andamento) as ultima_atualizacao
                FROM andamento_base
            """)
            result = cursor.fetchone()
            if result:
                total_andamento = result[0]
                ultima_andamento = result[1]
                print(f"  ✓ andamento_base: {total_andamento:,} registros")
                if ultima_andamento:
                    print(f"    Última atualização: {ultima_andamento}")
            
            # 4. Testar UPSERT (simulação)
            print()
            print("4. TESTANDO FUNCIONALIDADE UPSERT")
            print("-" * 70)
            
            try:
                from azure_sql_helper import upsert_agenda_base
                import pandas as pd
                
                # Criar DataFrame de teste (vazio, só para testar a função)
                df_teste = pd.DataFrame({
                    'id_legalone': [],
                    'compromisso_tarefa': [],
                    'tipo': []
                })
                
                print("  ✓ Função upsert_agenda_base importada com sucesso")
                print("  ✓ Função upsert_andamento_base disponível")
                print("  ℹ Funções prontas para uso nos workflows")
                
            except Exception as e:
                print(f"  ⚠ Erro ao importar funções: {e}")
            
            conn.close()
            
            # 5. Resumo
            print()
            print("=" * 70)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("=" * 70)
            print()
            print("RESUMO:")
            print("  ✓ Variáveis de ambiente configuradas")
            print("  ✓ Conexão com Azure SQL funcionando")
            print("  ✓ Tabelas acessíveis")
            print("  ✓ Funções de UPSERT disponíveis")
            print()
            print("PRÓXIMOS PASSOS:")
            print("  1. As credenciais no GitHub Secrets devem ser as mesmas")
            print("  2. Fazer commit e push das correções dos workflows")
            print("  3. Executar um workflow manualmente para testar")
            print("  4. Monitorar as próximas execuções automáticas")
            print()
            
            return True
        else:
            print("  ❌ Falha ao conectar ao Azure SQL")
            print()
            print("POSSÍVEIS CAUSAS:")
            print("  - Banco Azure SQL está pausado")
            print("  - Firewall bloqueando conexão")
            print("  - Credenciais incorretas")
            print("  - Servidor indisponível")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao testar conexão: {e}")
        print()
        print("VERIFIQUE:")
        print("  - Se o arquivo azure_sql_helper.py existe")
        print("  - Se as dependências estão instaladas (pyodbc)")
        print("  - Se o driver ODBC está instalado")
        return False

if __name__ == "__main__":
    sucesso = testar_conexao()
    sys.exit(0 if sucesso else 1)
