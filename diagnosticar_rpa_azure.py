"""
Script de diagnóstico para verificar por que o RPA não está atualizando o Azure SQL
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pyodbc

# Carregar variáveis de ambiente
load_dotenv('config.env')

def verificar_configuracao():
    """Verifica se as configurações do Azure SQL estão presentes"""
    print("=" * 70)
    print("1. VERIFICANDO CONFIGURAÇÕES")
    print("=" * 70)
    
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    
    configs = {
        "AZURE_SERVER": server,
        "AZURE_DATABASE": database,
        "AZURE_USER": username,
        "AZURE_PASSWORD": "***" if password else None
    }
    
    todas_ok = True
    for key, value in configs.items():
        if value:
            print(f"  ✓ {key}: {value if key != 'AZURE_PASSWORD' else '***'}")
        else:
            print(f"  ❌ {key}: NÃO CONFIGURADO")
            todas_ok = False
    
    print()
    return todas_ok, configs

def testar_conexao_azure():
    """Testa a conexão com o Azure SQL"""
    print("=" * 70)
    print("2. TESTANDO CONEXÃO COM AZURE SQL")
    print("=" * 70)
    
    try:
        from azure_sql_helper import get_azure_connection
        conn = get_azure_connection()
        
        if conn:
            print("  ✓ Conexão estabelecida com sucesso!")
            
            # Verificar última atualização
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 
                    MAX(created_at) as ultima_atualizacao,
                    COUNT(*) as total_registros
                FROM agenda_base
            """)
            
            result = cursor.fetchone()
            if result:
                ultima_atualizacao = result[0]
                total_registros = result[1]
                
                print(f"  ✓ Total de registros: {total_registros:,}")
                
                if ultima_atualizacao:
                    print(f"  ✓ Última atualização: {ultima_atualizacao}")
                    
                    # Verificar se está defasado
                    if isinstance(ultima_atualizacao, datetime):
                        dias_atras = (datetime.now() - ultima_atualizacao.replace(tzinfo=None)).days
                        horas_atras = (datetime.now() - ultima_atualizacao.replace(tzinfo=None)).total_seconds() / 3600
                        
                        print(f"  ⚠ Tempo desde última atualização: {dias_atras} dias ({horas_atras:.1f} horas)")
                        
                        if dias_atras > 1:
                            print(f"  ❌ BANCO ESTÁ DEFASADO! Mais de 1 dia sem atualização.")
                        elif horas_atras > 12:
                            print(f"  ⚠ Banco pode estar defasado (mais de 12 horas)")
                        else:
                            print(f"  ✓ Banco parece atualizado")
                else:
                    print("  ⚠ Não foi possível determinar última atualização")
            
            conn.close()
            return True
        else:
            print("  ❌ Falha ao conectar ao Azure SQL")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao testar conexão: {e}")
        return False

def verificar_ultimas_execucoes():
    """Verifica logs e arquivos de atualização"""
    print()
    print("=" * 70)
    print("3. VERIFICANDO ÚLTIMAS EXECUÇÕES")
    print("=" * 70)
    
    # Verificar arquivo de log de atualização
    log_file = "atualizacao_log.txt"
    if os.path.exists(log_file):
        print(f"  ✓ Arquivo de log encontrado: {log_file}")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"  ✓ Últimas 5 linhas do log:")
                    for line in lines[-5:]:
                        print(f"    {line.strip()}")
                else:
                    print("  ⚠ Arquivo de log está vazio")
        except Exception as e:
            print(f"  ⚠ Erro ao ler log: {e}")
    else:
        print(f"  ⚠ Arquivo de log não encontrado: {log_file}")
    
    # Verificar arquivos de download recentes
    downloads_dir = "downloads"
    if os.path.exists(downloads_dir):
        arquivos = [f for f in os.listdir(downloads_dir) if f.endswith(('.xlsx', '.xls'))]
        if arquivos:
            print(f"  ✓ {len(arquivos)} arquivo(s) encontrado(s) em downloads/")
            # Ordenar por data de modificação
            arquivos_com_data = []
            for arquivo in arquivos:
                caminho = os.path.join(downloads_dir, arquivo)
                mtime = os.path.getmtime(caminho)
                arquivos_com_data.append((arquivo, datetime.fromtimestamp(mtime)))
            
            arquivos_com_data.sort(key=lambda x: x[1], reverse=True)
            
            print(f"  ✓ Arquivos mais recentes:")
            for arquivo, data in arquivos_com_data[:3]:
                print(f"    - {arquivo} ({data.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print(f"  ⚠ Nenhum arquivo Excel encontrado em downloads/")
    else:
        print(f"  ⚠ Pasta downloads/ não encontrada")

def verificar_scripts_rpa():
    """Verifica se os scripts RPA principais existem"""
    print()
    print("=" * 70)
    print("4. VERIFICANDO SCRIPTS RPA")
    print("=" * 70)
    
    scripts = [
        "rpa_agenda_rmb.py",
        "rpa_atualiza_concluidos_rmb.py",
        "rpa_atualiza_agenda_677_rmb.py",
        "rpa_atualiza_cumpridos_com_parecer_rmb.py",
        "rpa_andamentos_completo.py",
        "azure_sql_helper.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            print(f"  ✓ {script}")
        else:
            print(f"  ❌ {script} - NÃO ENCONTRADO")

def verificar_github_workflows():
    """Verifica se os workflows do GitHub Actions estão configurados"""
    print()
    print("=" * 70)
    print("5. VERIFICANDO GITHUB WORKFLOWS")
    print("=" * 70)
    
    workflows_dir = ".github/workflows"
    if os.path.exists(workflows_dir):
        workflows = [f for f in os.listdir(workflows_dir) if f.endswith('.yml')]
        if workflows:
            print(f"  ✓ {len(workflows)} workflow(s) encontrado(s):")
            for workflow in workflows:
                print(f"    - {workflow}")
        else:
            print(f"  ⚠ Nenhum workflow encontrado")
    else:
        print(f"  ⚠ Pasta .github/workflows não encontrada")
        print(f"  ⚠ Os workflows podem não estar configurados localmente")

def main():
    print("\n" + "=" * 70)
    print("DIAGNÓSTICO: POR QUE O RPA NÃO ESTÁ ATUALIZANDO O AZURE SQL?")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar configurações
    configs_ok, configs = verificar_configuracao()
    
    if not configs_ok:
        print("\n❌ ERRO: Configurações incompletas no config.env!")
        print("   Corrija as configurações antes de continuar.")
        return
    
    # 2. Testar conexão
    conexao_ok = testar_conexao_azure()
    
    # 3. Verificar execuções
    verificar_ultimas_execucoes()
    
    # 4. Verificar scripts
    verificar_scripts_rpa()
    
    # 5. Verificar workflows
    verificar_github_workflows()
    
    # Resumo
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if not conexao_ok:
        print("❌ PROBLEMA CRÍTICO: Não foi possível conectar ao Azure SQL")
        print("   Possíveis causas:")
        print("   - Credenciais incorretas")
        print("   - Servidor Azure SQL indisponível")
        print("   - Firewall bloqueando conexão")
        print("   - Driver ODBC não instalado")
    else:
        print("✓ Conexão com Azure SQL funcionando")
    
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Verifique se os GitHub Actions estão executando")
    print("2. Verifique os logs de execução no GitHub")
    print("3. Execute manualmente um script RPA para testar")
    print("4. Verifique se há erros silenciosos nos scripts")
    print()

if __name__ == "__main__":
    main()
