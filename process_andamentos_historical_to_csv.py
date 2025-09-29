#!/usr/bin/env python3
"""
Processa arquivo histórico de andamentos e exporta como CSV
Aplica os tratamentos específicos para andamentos conforme especificação da tabela
"""

import os
import pandas as pd
from datetime import datetime

def extract_date_from_datetime(datetime_str):
    """Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss e converte para aaaa/mm/dd"""
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        # Retorna no formato aaaa/mm/dd
        return dt.strftime('%Y/%m/%d')
    except:
        return None

def process_andamentos_historical_file():
    """Processa arquivo histórico de andamentos e exporta como CSV com merge do arquivo de agenda"""
    print("🔄 PROCESSAMENTO DE ARQUIVO HISTÓRICO DE ANDAMENTOS COM MERGE")
    print("="*80)
    
    # Caminhos dos arquivos
    andamentos_file = r"C:\Users\cleit\Desktop\PROCESSAMENTO\z-rpa_andamentos_agenda_rmb_queeue_hitorico.xlsx"
    agenda_file = r"C:\Users\cleit\Desktop\PROCESSAMENTO\z-rpa_agenda_rmb_queeue_historico.xlsx"
    output_file = r"C:\Users\cleit\Desktop\PROCESSAMENTO\z-rpa_andamentos_agenda_rmb_queeue_hitorico_processed.csv"
    
    # 1. Verificar se arquivos existem
    print(f"📖 Verificando arquivo de andamentos: {andamentos_file}")
    if not os.path.exists(andamentos_file):
        print(f"❌ Arquivo de andamentos não encontrado: {andamentos_file}")
        print("🔧 Verifique se o arquivo está no local correto")
        return False
    
    print(f"📖 Verificando arquivo de agenda: {agenda_file}")
    if not os.path.exists(agenda_file):
        print(f"❌ Arquivo de agenda não encontrado: {agenda_file}")
        print("🔧 Verifique se o arquivo está no local correto")
        return False
    
    print("✅ Ambos os arquivos encontrados!")
    
    try:
        # 2. Carregar arquivos Excel
        print("📖 Carregando arquivo de andamentos...")
        df_andamentos = pd.read_excel(andamentos_file)
        print(f"✅ Arquivo de andamentos carregado: {len(df_andamentos)} linhas, {len(df_andamentos.columns)} colunas")
        print(f"📋 Colunas do arquivo de andamentos: {df_andamentos.columns.tolist()}")
        
        print("📖 Carregando arquivo de agenda...")
        df_agenda = pd.read_excel(agenda_file)
        print(f"✅ Arquivo de agenda carregado: {len(df_agenda)} linhas, {len(df_agenda.columns)} colunas")
        print(f"📋 Colunas do arquivo de agenda: {df_agenda.columns.tolist()}")
        
        # 3. Fazer merge dos arquivos
        print("\n🔄 Fazendo merge dos arquivos...")
        print("🔍 Comparando id_agenda_legalone (andamentos) com id_legalone (agenda)")
        
        # Verificar se as colunas existem
        if 'id_agenda_legalone' not in df_andamentos.columns:
            print("❌ Coluna 'id_agenda_legalone' não encontrada no arquivo de andamentos")
            return False
            
        if 'id_legalone' not in df_agenda.columns:
            print("❌ Coluna 'id_legalone' não encontrada no arquivo de agenda")
            return False
        
        # Fazer o merge (inner join)
        df_merged = pd.merge(
            df_andamentos, 
            df_agenda[['id_legalone']], 
            left_on='id_agenda_legalone', 
            right_on='id_legalone', 
            how='inner'
        )
        
        print(f"✅ Merge concluído: {len(df_merged)} andamentos com correspondência encontrados")
        print(f"📊 Andamentos originais: {len(df_andamentos)}")
        print(f"📊 Andamentos com correspondência: {len(df_merged)}")
        print(f"📊 Taxa de correspondência: {len(df_merged)/len(df_andamentos)*100:.1f}%")
        
        # Usar o DataFrame merged para processamento
        df = df_merged
        
        # 4. Aplicar tratamentos conforme especificação da tabela
        print("\n🔄 Aplicando tratamentos aos dados...")
        df_processed = pd.DataFrame()
        
        # 4.1. Mapeamento direto das colunas conforme tabela
        direct_mappings = {
            'id_agenda_legalone': 'id_agenda_legalone',
            'id_andamento_legalone': 'id_andamento_legalone',
            'tipo_andamento': 'tipo_andamento',
            'subtipo_andamento': 'subtipo_andamento',
            'descricao_andamento': 'descricao_andamento'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"✅ Coluna '{excel_col}' → '{supabase_col}'")
            else:
                print(f"⚠️ Coluna '{excel_col}' não encontrada no arquivo")
                df_processed[supabase_col] = None
        
        # 4.2. Tratamento especial para campo 'cadastro_andamento'
        print("\n🔄 Processando campo 'cadastro_andamento'...")
        if 'cadastro_andamento' in df.columns:
            # Aplicar transformação: dd/mm/aaaa hh:mm:ss → aaaa/mm/dd
            df_processed['cadastro_andamento'] = df['cadastro_andamento'].apply(extract_date_from_datetime)
            print("✅ Campo 'cadastro_andamento' processado (dd/mm/aaaa hh:mm:ss → aaaa/mm/dd)")
        else:
            print("⚠️ Coluna 'cadastro_andamento' não encontrada no arquivo")
            df_processed['cadastro_andamento'] = None
        
        # 4.3. Limpar dados e converter tipos conforme especificação
        print("\n🔄 Limpando dados e convertendo tipos...")
        
        # Converter campos int8
        int8_columns = ['id_agenda_legalone', 'id_andamento_legalone']
        for col in int8_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').astype('Int64')
                print(f"✅ Campo '{col}' convertido para int8")
        
        # Converter campos text
        text_columns = ['tipo_andamento', 'subtipo_andamento', 'descricao_andamento']
        for col in text_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].astype(str)
                print(f"✅ Campo '{col}' convertido para text")
        
        # Converter campo date (cadastro_andamento já está no formato correto)
        if 'cadastro_andamento' in df_processed.columns:
            # Verificar se há valores válidos
            valid_dates = df_processed['cadastro_andamento'].notna().sum()
            print(f"✅ Campo 'cadastro_andamento' processado: {valid_dates} datas válidas")
        
        print(f"\n✅ Processamento concluído: {len(df_processed)} linhas processadas")
        print(f"📊 Colunas finais: {df_processed.columns.tolist()}")
        
        # 5. Exportar como CSV
        print(f"\n💾 Exportando como CSV: {output_file}")
        df_processed.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Arquivo CSV salvo com sucesso!")
        
        # 6. Relatório final
        print(f"\n📊 RELATÓRIO FINAL:")
        print("="*50)
        print(f"📖 Arquivo de andamentos: {andamentos_file}")
        print(f"📖 Arquivo de agenda: {agenda_file}")
        print(f"💾 Arquivo processado: {output_file}")
        print(f"📊 Linhas processadas: {len(df_processed)}")
        print(f"📋 Colunas finais: {len(df_processed.columns)}")
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar primeiras linhas
        print(f"\n📋 PRIMEIRAS 3 LINHAS DO ARQUIVO PROCESSADO:")
        print("="*70)
        print(df_processed.head(3).to_string())
        
        # Mostrar estatísticas por coluna
        print(f"\n📊 ESTATÍSTICAS POR COLUNA:")
        print("="*50)
        for col in df_processed.columns:
            non_null = df_processed[col].notna().sum()
            total = len(df_processed)
            print(f"  {col}: {non_null}/{total} valores não nulos")
        
        print(f"\n🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("✅ Arquivo histórico de andamentos processado")
        print("✅ Merge realizado com arquivo de agenda")
        print("✅ Apenas andamentos com correspondência extraídos")
        print("✅ Tratamentos aplicados conforme especificação")
        print("✅ Arquivo CSV exportado")
        print("✅ Pronto para importação no banco de dados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PROCESSADOR DE ARQUIVO HISTÓRICO DE ANDAMENTOS COM MERGE")
    print("Este script processa o arquivo histórico de andamentos com merge do arquivo de agenda")
    print("Extrai apenas andamentos que tenham correspondência com registros da agenda")
    print("Seguindo as especificações da tabela de mapeamento")
    print("")
    
    process_andamentos_historical_file()
