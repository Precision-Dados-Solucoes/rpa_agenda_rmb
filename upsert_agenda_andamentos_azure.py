"""
Script para fazer UPSERT de agenda e andamentos no Azure SQL
Lê arquivos Excel e atualiza o banco
"""

import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('config.env')

# Importar funções de upsert
from azure_sql_helper import (
    get_azure_connection,
    upsert_agenda_base,
    upsert_andamento_base
)

def processar_arquivo_agenda(caminho_arquivo):
    """Processa arquivo Excel de agenda e faz upsert no Azure SQL"""
    print("=" * 70)
    print("PROCESSANDO AGENDA")
    print("=" * 70)
    print(f"Arquivo: {caminho_arquivo}")
    print()
    
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return False
    
    try:
        # Ler arquivo Excel
        print("Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"✓ {len(df):,} registros carregados")
        print()
        
        # Verificar colunas necessárias
        coluna_id = 'id_legalone'
        if coluna_id not in df.columns:
            print(f"❌ Coluna '{coluna_id}' não encontrada no arquivo")
            print(f"Colunas disponíveis: {', '.join(df.columns)}")
            return False
        
        # Mostrar preview
        print("Preview dos dados:")
        print(df.head(3).to_string())
        print()
        
        # Fazer upsert no Azure SQL
        print("Fazendo UPSERT no Azure SQL...")
        sucesso = upsert_agenda_base(df, "agenda_base", "id_legalone")
        
        if sucesso:
            print()
            print("✅ AGENDA ATUALIZADA COM SUCESSO!")
            return True
        else:
            print()
            print("❌ FALHA AO ATUALIZAR AGENDA")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return False

def processar_arquivo_andamentos(caminho_arquivo):
    """Processa arquivo Excel de andamentos e faz upsert no Azure SQL"""
    print("=" * 70)
    print("PROCESSANDO ANDAMENTOS")
    print("=" * 70)
    print(f"Arquivo: {caminho_arquivo}")
    print()
    
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return False
    
    try:
        # Ler arquivo Excel
        print("Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"✓ {len(df):,} registros carregados")
        print()
        
        # Verificar colunas necessárias
        coluna_id = 'id_andamento_legalone'
        if coluna_id not in df.columns:
            print(f"❌ Coluna '{coluna_id}' não encontrada no arquivo")
            print(f"Colunas disponíveis: {', '.join(df.columns)}")
            return False
        
        # Mostrar preview
        print("Preview dos dados:")
        print(df.head(3).to_string())
        print()
        
        # Fazer upsert no Azure SQL
        print("Fazendo UPSERT no Azure SQL...")
        sucesso = upsert_andamento_base(df, "andamento_base", "id_andamento_legalone")
        
        if sucesso:
            print()
            print("✅ ANDAMENTOS ATUALIZADOS COM SUCESSO!")
            return True
        else:
            print()
            print("❌ FALHA AO ATUALIZAR ANDAMENTOS")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 70)
    print("UPSERT DE AGENDA E ANDAMENTOS NO AZURE SQL")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar conexão primeiro
    print("Verificando conexão com Azure SQL...")
    conn = get_azure_connection()
    if not conn:
        print("❌ Não foi possível conectar ao Azure SQL")
        print("   Verifique as credenciais no config.env")
        return
    conn.close()
    print("✓ Conexão OK")
    print()
    
    # Solicitar caminhos dos arquivos
    print("Por favor, informe os caminhos dos arquivos Excel:")
    print()
    
    # Arquivo de agenda
    caminho_agenda = input("Caminho do arquivo de AGENDA (ou Enter para pular): ").strip()
    if caminho_agenda:
        # Se não for caminho absoluto, tentar na pasta downloads
        if not os.path.isabs(caminho_agenda):
            caminho_agenda_tentativa = os.path.join("downloads", caminho_agenda)
            if os.path.exists(caminho_agenda_tentativa):
                caminho_agenda = caminho_agenda_tentativa
        
        sucesso_agenda = processar_arquivo_agenda(caminho_agenda)
    else:
        print("⏭ Pulando agenda...")
        sucesso_agenda = None
    
    print()
    
    # Arquivo de andamentos
    caminho_andamentos = input("Caminho do arquivo de ANDAMENTOS (ou Enter para pular): ").strip()
    if caminho_andamentos:
        # Se não for caminho absoluto, tentar na pasta downloads
        if not os.path.isabs(caminho_andamentos):
            caminho_andamentos_tentativa = os.path.join("downloads", caminho_andamentos)
            if os.path.exists(caminho_andamentos_tentativa):
                caminho_andamentos = caminho_andamentos_tentativa
        
        sucesso_andamentos = processar_arquivo_andamentos(caminho_andamentos)
    else:
        print("⏭ Pulando andamentos...")
        sucesso_andamentos = None
    
    # Resumo final
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if sucesso_agenda is not None:
        if sucesso_agenda:
            print("✅ Agenda: Atualizada com sucesso")
        else:
            print("❌ Agenda: Falha na atualização")
    else:
        print("⏭ Agenda: Não processada")
    
    if sucesso_andamentos is not None:
        if sucesso_andamentos:
            print("✅ Andamentos: Atualizados com sucesso")
        else:
            print("❌ Andamentos: Falha na atualização")
    else:
        print("⏭ Andamentos: Não processados")
    
    print()
    
    # Verificar status final
    if (sucesso_agenda is None or sucesso_agenda) and (sucesso_andamentos is None or sucesso_andamentos):
        print("✅ Processo concluído!")
        print()
        print("Próximo passo: Fazer commit das alterações")
    else:
        print("⚠ Alguns processos falharam. Verifique os erros acima.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
