"""
Script para fazer UPSERT dos arquivos de atualização no Azure SQL
Arquivos: atualizacao/agenda.xlsx e atualizacao/andamentos.xlsx
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

def processar_agenda():
    """Processa arquivo de agenda"""
    caminho_arquivo = "atualizacao/agenda.xlsx"
    
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
        print("📖 Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"✅ {len(df):,} registros carregados")
        print()
        
        # Verificar colunas
        print("📋 Colunas encontradas:")
        for col in df.columns:
            print(f"   - {col}")
        print()
        
        # Verificar coluna obrigatória
        if 'id_legalone' not in df.columns:
            print(f"❌ Coluna 'id_legalone' não encontrada no arquivo")
            print(f"   Colunas disponíveis: {', '.join(df.columns)}")
            return False
        
        # Mostrar preview
        print("👀 Preview dos dados (primeiras 3 linhas):")
        print(df[['id_legalone'] + [col for col in df.columns if col != 'id_legalone'][:4]].head(3).to_string())
        print()
        
        # Fazer upsert no Azure SQL
        print("🔄 Fazendo UPSERT no Azure SQL (tabela: agenda_base)...")
        print("   Isso pode levar alguns minutos...")
        print()
        
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

def processar_andamentos():
    """Processa arquivo de andamentos"""
    caminho_arquivo = "atualizacao/andamentos.xlsx"
    
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
        print("📖 Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"✅ {len(df):,} registros carregados")
        print()
        
        # Verificar colunas
        print("📋 Colunas encontradas:")
        for col in df.columns:
            print(f"   - {col}")
        print()
        
        # Verificar coluna obrigatória
        if 'id_andamento_legalone' not in df.columns:
            print(f"❌ Coluna 'id_andamento_legalone' não encontrada no arquivo")
            print(f"   Colunas disponíveis: {', '.join(df.columns)}")
            return False
        
        # Mostrar preview
        print("👀 Preview dos dados (primeiras 3 linhas):")
        preview_cols = ['id_andamento_legalone'] + [col for col in df.columns if col != 'id_andamento_legalone'][:4]
        print(df[preview_cols].head(3).to_string())
        print()
        
        # Fazer upsert no Azure SQL
        print("🔄 Fazendo UPSERT no Azure SQL (tabela: andamento_base)...")
        print("   Isso pode levar alguns minutos...")
        print()
        
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
    
    # Verificar conexão primeiro (com retry)
    print("🔌 Verificando conexão com Azure SQL...")
    import time
    max_tentativas = 5
    intervalo = 10
    
    conn = None
    for tentativa in range(1, max_tentativas + 1):
        print(f"   Tentativa {tentativa}/{max_tentativas}...")
        conn = get_azure_connection()
        if conn:
            print("✅ Conexão estabelecida!")
            conn.close()
            break
        else:
            if tentativa < max_tentativas:
                print(f"   ⏳ Aguardando {intervalo} segundos antes da próxima tentativa...")
                time.sleep(intervalo)
    
    if not conn:
        print("❌ Não foi possível conectar ao Azure SQL após {max_tentativas} tentativas")
        print("   O banco pode estar pausado. Verifique no Portal Azure.")
        return
    
    print()
    
    # Processar agenda
    print("📋 PROCESSANDO AGENDA")
    print("-" * 70)
    sucesso_agenda = processar_agenda()
    
    print()
    print()
    
    # Processar andamentos
    print("📋 PROCESSANDO ANDAMENTOS")
    print("-" * 70)
    sucesso_andamentos = processar_andamentos()
    
    # Resumo final
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print()
    
    if sucesso_agenda:
        print("✅ Agenda: Atualizada com sucesso na tabela agenda_base")
    else:
        print("❌ Agenda: Falha na atualização")
    
    if sucesso_andamentos:
        print("✅ Andamentos: Atualizados com sucesso na tabela andamento_base")
    else:
        print("❌ Andamentos: Falha na atualização")
    
    print()
    
    if sucesso_agenda and sucesso_andamentos:
        print("🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        print()
        print("Próximo passo: Fazer commit das alterações")
    elif sucesso_agenda or sucesso_andamentos:
        print("⚠ Processo parcialmente concluído")
        print("   Verifique os erros acima")
    else:
        print("❌ Processo falhou")
        print("   Verifique os erros acima")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
