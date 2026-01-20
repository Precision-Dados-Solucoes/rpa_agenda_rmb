"""
Script automático para fazer UPSERT de agenda e andamentos no Azure SQL
Procura arquivos Excel na pasta downloads e processa automaticamente
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('config.env')

# Importar funções de upsert
from azure_sql_helper import (
    get_azure_connection,
    upsert_agenda_base,
    upsert_andamento_base
)

def encontrar_arquivos_excel():
    """Encontra arquivos Excel na pasta downloads"""
    downloads_dir = Path("downloads")
    
    if not downloads_dir.exists():
        print(f"⚠ Pasta downloads não encontrada. Criando...")
        downloads_dir.mkdir(exist_ok=True)
        return [], []
    
    # Procurar arquivos de agenda
    arquivos_agenda = list(downloads_dir.glob("*agenda*.xlsx")) + \
                     list(downloads_dir.glob("*agenda*.xls"))
    
    # Procurar arquivos de andamentos
    arquivos_andamentos = list(downloads_dir.glob("*andamento*.xlsx")) + \
                         list(downloads_dir.glob("*andamento*.xls"))
    
    # Ordenar por data de modificação (mais recente primeiro)
    arquivos_agenda.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    arquivos_andamentos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return arquivos_agenda, arquivos_andamentos

def processar_agenda(caminho_arquivo):
    """Processa arquivo Excel de agenda"""
    print(f"\n📄 Processando: {caminho_arquivo.name}")
    
    try:
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"   ✓ {len(df):,} registros carregados")
        
        if 'id_legalone' not in df.columns:
            print(f"   ❌ Coluna 'id_legalone' não encontrada")
            return False
        
        sucesso = upsert_agenda_base(df, "agenda_base", "id_legalone")
        
        if sucesso:
            print(f"   ✅ Agenda atualizada com sucesso!")
            return True
        else:
            print(f"   ❌ Falha ao atualizar agenda")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def processar_andamentos(caminho_arquivo):
    """Processa arquivo Excel de andamentos"""
    print(f"\n📄 Processando: {caminho_arquivo.name}")
    
    try:
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"   ✓ {len(df):,} registros carregados")
        
        if 'id_andamento_legalone' not in df.columns:
            print(f"   ❌ Coluna 'id_andamento_legalone' não encontrada")
            return False
        
        sucesso = upsert_andamento_base(df, "andamento_base", "id_andamento_legalone")
        
        if sucesso:
            print(f"   ✅ Andamentos atualizados com sucesso!")
            return True
        else:
            print(f"   ❌ Falha ao atualizar andamentos")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("UPSERT AUTOMÁTICO - AGENDA E ANDAMENTOS")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar conexão
    print("🔌 Verificando conexão com Azure SQL...")
    conn = get_azure_connection()
    if not conn:
        print("❌ Não foi possível conectar ao Azure SQL")
        return
    conn.close()
    print("✅ Conexão OK")
    print()
    
    # Encontrar arquivos
    print("🔍 Procurando arquivos Excel na pasta downloads...")
    arquivos_agenda, arquivos_andamentos = encontrar_arquivos_excel()
    
    print(f"\n📊 Arquivos encontrados:")
    print(f"   Agenda: {len(arquivos_agenda)} arquivo(s)")
    if arquivos_agenda:
        for arquivo in arquivos_agenda[:3]:  # Mostrar até 3
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime)
            print(f"      - {arquivo.name} ({data_mod.strftime('%Y-%m-%d %H:%M')})")
    
    print(f"   Andamentos: {len(arquivos_andamentos)} arquivo(s)")
    if arquivos_andamentos:
        for arquivo in arquivos_andamentos[:3]:  # Mostrar até 3
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime)
            print(f"      - {arquivo.name} ({data_mod.strftime('%Y-%m-%d %H:%M')})")
    
    if not arquivos_agenda and not arquivos_andamentos:
        print("\n⚠ Nenhum arquivo encontrado na pasta downloads")
        print("   Coloque os arquivos Excel na pasta 'downloads' e execute novamente")
        return
    
    print()
    
    # Processar agenda
    sucesso_agenda = None
    if arquivos_agenda:
        arquivo_mais_recente = arquivos_agenda[0]
        print(f"📋 Processando agenda (arquivo mais recente)...")
        sucesso_agenda = processar_agenda(arquivo_mais_recente)
    else:
        print("⏭ Nenhum arquivo de agenda encontrado")
    
    # Processar andamentos
    sucesso_andamentos = None
    if arquivos_andamentos:
        arquivo_mais_recente = arquivos_andamentos[0]
        print(f"\n📋 Processando andamentos (arquivo mais recente)...")
        sucesso_andamentos = processar_andamentos(arquivo_mais_recente)
    else:
        print("\n⏭ Nenhum arquivo de andamentos encontrado")
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if sucesso_agenda is not None:
        print("✅ Agenda: Atualizada" if sucesso_agenda else "❌ Agenda: Falha")
    else:
        print("⏭ Agenda: Não processada")
    
    if sucesso_andamentos is not None:
        print("✅ Andamentos: Atualizados" if sucesso_andamentos else "❌ Andamentos: Falha")
    else:
        print("⏭ Andamentos: Não processados")
    
    print()
    
    if (sucesso_agenda is None or sucesso_agenda) and (sucesso_andamentos is None or sucesso_andamentos):
        print("✅ Processo concluído com sucesso!")
        print("\nPróximo passo: Fazer commit das alterações")
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
