#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar tabela agenda_base no Supabase e MySQL Hostinger
- Carrega arquivo atualizar_Agenda_1612.xlsx da pasta Downloads
- Processa dados usando as mesmas funções do rpa_agenda_rmb.py
- Executa UPSERT na tabela agenda_base (baseado em id_legalone)
- Ao final, a tabela deve conter 7209 registros
"""

import sys
import io
# Configurar encoding UTF-8 para stdout
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import os
import asyncio
import asyncpg
from pathlib import Path
from dotenv import load_dotenv
from hostinger_mysql_helper import upsert_agenda_base as upsert_agenda_base_hostinger

load_dotenv('config.env')

def read_excel_file(file_path):
    """
    Lê um arquivo Excel e retorna um DataFrame do pandas.
    """
    print(f"📂 Lendo o arquivo: {file_path}")
    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, forneça um arquivo .xlsx ou .csv")
        
        print(f"✅ Arquivo '{file_path}' lido com sucesso.")
        print(f"📊 Total de linhas: {len(df)}")
        print(f"📊 Total de colunas: {len(df.columns)}")
        print(f"\n📋 Colunas do DataFrame:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        return df
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo não encontrado em {file_path}")
        return None
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo Excel: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_date_from_datetime(datetime_str):
    """
    Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss ou dd/mm/aaaa hh:mm
    Tenta primeiro com segundos, depois sem segundos
    Também trata timestamps do Excel
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Se já for um objeto datetime do pandas
        if hasattr(datetime_str, 'date'):
            return datetime_str.date()
        
        # Se já for um objeto date
        if hasattr(datetime_str, 'year'):
            return datetime_str
        
        # Se for número (timestamp do Excel), converter
        if isinstance(datetime_str, (int, float)):
            # Excel usa 1899-12-30 como origem
            dt = pd.to_datetime(datetime_str, unit='d', origin='1899-12-30', errors='coerce')
            if not pd.isna(dt):
                return dt.date()
            # Tenta como timestamp Unix
            dt = pd.to_datetime(datetime_str, unit='s', errors='coerce')
            if not pd.isna(dt):
                return dt.date()
        
        # Se for string, tentar converter
        if isinstance(datetime_str, str):
            # Tenta primeiro com segundos (formato padrão)
            dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
            if pd.isna(dt):
                # Se falhar, tenta sem segundos (formato prazo_fatal)
                dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M', errors='coerce')
            if pd.isna(dt):
                # Tenta formato genérico
                dt = pd.to_datetime(datetime_str, errors='coerce')
            if not pd.isna(dt):
                return dt.date()
        return None
    except Exception as e:
        return None

def extract_time_from_datetime(datetime_str):
    """
    Extrai a hora de uma string no formato dd/mm/aaaa hh:mm:ss
    Também trata timestamps do Excel
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Se já for um objeto datetime do pandas
        if hasattr(datetime_str, 'time'):
            return datetime_str.time()
        
        # Se já for um objeto time
        if hasattr(datetime_str, 'hour'):
            return datetime_str
        
        # Se for número (timestamp do Excel), converter
        if isinstance(datetime_str, (int, float)):
            # Excel usa 1899-12-30 como origem
            dt = pd.to_datetime(datetime_str, unit='d', origin='1899-12-30', errors='coerce')
            if not pd.isna(dt):
                return dt.time()
            # Tenta como timestamp Unix
            dt = pd.to_datetime(datetime_str, unit='s', errors='coerce')
            if not pd.isna(dt):
                return dt.time()
        
        # Se for string, tentar converter
        if isinstance(datetime_str, str):
            dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
            if pd.isna(dt):
                dt = pd.to_datetime(datetime_str, errors='coerce')
            if not pd.isna(dt):
                return dt.time()
        return None
    except Exception as e:
        return None

def generate_link(id_legalone):
    """
    Gera o link concatenado baseado no id_legalone
    """
    if pd.isna(id_legalone):
        return None
    
    base_url = "https://robertomatos.novajus.com.br/agenda/compromissos/DetailsCompromissoTarefa/"
    params = "?hasNavigation=True&currentPage=1&returnUrl=%2Fagenda%2FCompromissoTarefa%2FSearch"
    
    return f"{base_url}{id_legalone}{params}"

def clean_value_for_db(value):
    """
    Limpa valores do pandas para tipos nativos do Python compatíveis com asyncpg
    """
    if pd.isna(value) or value is None:
        return None
    
    # Converter Int64 do pandas para int nativo
    if hasattr(value, 'item'):  # Tipos numpy/pandas
        try:
            return value.item()
        except:
            pass
    
    # Converter strings "nan", "None", etc.
    if isinstance(value, str) and value.lower() in ['nan', 'none', '']:
        return None
    
    # Manter tipos nativos (int, str, date, time, datetime)
    return value

def process_excel_file(file_path):
    """
    Processa o arquivo Excel com todos os tratamentos necessários.
    Baseado na função do rpa_agenda_rmb.py
    """
    print("🔄 Iniciando processamento do arquivo Excel...")
    
    # 1. Ler o arquivo
    df = read_excel_file(file_path)
    if df is None or df.empty:
        print("❌ Erro: Não foi possível ler o arquivo ou arquivo vazio.")
        return None
    
    print(f"📊 Arquivo lido com sucesso. Linhas: {len(df)}")
    
    try:
        # 2. Criar DataFrame processado com as colunas do Supabase
        df_processed = pd.DataFrame()
        
        # Mapeamento direto (sem tratamento)
        # Formato: {coluna_excel: coluna_supabase}
        direct_mappings = {
            'id_legalone': 'id_legalone',
            'compromisso_tarefa': 'compromisso_tarefa', 
            'tipo': 'tipo',
            'subtipo': 'subtipo',
            'etiqueta': 'etiqueta',
            'Pasta_proc': 'pasta_proc',  # Excel tem Pasta_proc, banco tem pasta_proc
            'pasta_proc': 'pasta_proc',  # Caso já esteja minúsculo
            'numero_cnj': 'numero_cnj',
            'executante': 'executante',
            'executante_sim': 'executante_sim',
            'descricao': 'descricao',
            'status': 'status'
        }
        
        # Copiar colunas diretas
        print("📋 Copiando colunas diretas...")
        for excel_col, supabase_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"✅ Coluna '{excel_col}' → '{supabase_col}'")
            elif supabase_col in df.columns:
                # Se a coluna já está no formato do banco
                df_processed[supabase_col] = df[supabase_col]
                print(f"✅ Coluna '{supabase_col}' já existe no formato correto")
        
        # Verificar se pasta_proc foi mapeada
        if 'pasta_proc' not in df_processed.columns:
            print("⚠️ Coluna 'pasta_proc' não foi mapeada")
        
        # 3. Tratamento de campos de data/hora
        print("\n📅 Processando campos de data/hora...")
        
        # Tratar campo 'inicio' (dd/mm/aaaa hh:mm:ss)
        if 'inicio' in df.columns:
            df_processed['inicio_data'] = df['inicio'].apply(extract_date_from_datetime)
            df_processed['inicio_hora'] = df['inicio'].apply(extract_time_from_datetime)
            print("✅ Campo 'inicio' processado → 'inicio_data' e 'inicio_hora'")
        else:
            print("⚠️ Coluna 'inicio' não encontrada")
            df_processed['inicio_data'] = None
            df_processed['inicio_hora'] = None
        
        # Tratar campo 'conclusao_prevista' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_prevista' in df.columns:
            df_processed['conclusao_prevista_data'] = df['conclusao_prevista'].apply(extract_date_from_datetime)
            df_processed['conclusao_prevista_hora'] = df['conclusao_prevista'].apply(extract_time_from_datetime)
            print("✅ Campo 'conclusao_prevista' processado → 'conclusao_prevista_data' e 'conclusao_prevista_hora'")
        else:
            print("⚠️ Coluna 'conclusao_prevista' não encontrada")
            df_processed['conclusao_prevista_data'] = None
            df_processed['conclusao_prevista_hora'] = None
        
        # Tratar campo 'conclusao_efetiva' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_efetiva' in df.columns:
            df_processed['conclusao_efetiva_data'] = df['conclusao_efetiva'].apply(extract_date_from_datetime)
            print("✅ Campo 'conclusao_efetiva' processado → 'conclusao_efetiva_data'")
        else:
            print("⚠️ Coluna 'conclusao_efetiva' não encontrada")
            df_processed['conclusao_efetiva_data'] = None
        
        # Tratar campo 'cadastro' (dd/mm/aaaa hh:mm:ss) → formato aaaa/mm/dd
        if 'cadastro' in df.columns:
            df_processed['cadastro'] = df['cadastro'].apply(extract_date_from_datetime)
            print("✅ Campo 'cadastro' processado → formato aaaa/mm/dd")
        else:
            print("⚠️ Coluna 'cadastro' não encontrada")
            df_processed['cadastro'] = None
        
        # Tratar campo 'prazo_fatal' (dd/mm/aaaa hh:mm) → apenas data
        if 'prazo_fatal' in df.columns:
            df_processed['prazo_fatal_data'] = df['prazo_fatal'].apply(extract_date_from_datetime)
            print("✅ Campo 'prazo_fatal' processado → 'prazo_fatal_data'")
        else:
            print("⚠️ Coluna 'prazo_fatal' não encontrada")
            df_processed['prazo_fatal_data'] = None
        
        # 4. Gerar campo 'link' concatenado
        if 'id_legalone' in df_processed.columns:
            df_processed['link'] = df_processed['id_legalone'].apply(generate_link)
            print("✅ Campo 'link' gerado com sucesso")
        else:
            print("⚠️ Coluna 'id_legalone' não encontrada, não foi possível gerar 'link'")
            df_processed['link'] = None
        
        # 5. Filtrar apenas linhas onde executante_sim = "Sim" (OPCIONAL - comentado para manter todos os registros)
        # print("🔄 Filtrando linhas onde executante_sim = 'Sim'...")
        # if 'executante_sim' in df_processed.columns:
        #     linhas_antes = len(df_processed)
        #     df_processed = df_processed[df_processed['executante_sim'] == 'Sim']
        #     linhas_depois = len(df_processed)
        #     print(f"✅ Filtro aplicado: {linhas_antes} → {linhas_depois} linhas (removidas {linhas_antes - linhas_depois} linhas com 'Não')")
        # else:
        #     print("⚠️ Coluna 'executante_sim' não encontrada, pulando filtro")
        
        # 6. Limpar dados nulos e converter tipos
        print("\n🔄 Limpando dados e convertendo tipos...")
        
        # Converter id_legalone para int8
        if 'id_legalone' in df_processed.columns:
            df_processed['id_legalone'] = pd.to_numeric(df_processed['id_legalone'], errors='coerce').astype('Int64')
            print("✅ Campo 'id_legalone' convertido para Int64")
        
        # Converter campos numéricos para string (text no Supabase)
        text_columns = ['pasta_proc', 'numero_cnj', 'executante', 'executante_sim', 'descricao', 'link', 'status', 'compromisso_tarefa', 'tipo', 'subtipo', 'etiqueta']
        for col in text_columns:
            if col in df_processed.columns:
                # Converter para string, tratando NaN
                df_processed[col] = df_processed[col].apply(
                    lambda x: None if pd.isna(x) else str(x) if x not in ['nan', 'None', ''] else None
                )
                print(f"✅ Campo '{col}' convertido para string")
        
        # Converter campos de data (já devem estar como date após extract_date_from_datetime)
        date_columns = ['inicio_data', 'conclusao_prevista_data', 'conclusao_efetiva_data', 'prazo_fatal_data', 'cadastro']
        for col in date_columns:
            if col in df_processed.columns:
                # Garantir que valores None/NaT sejam None
                df_processed[col] = df_processed[col].apply(lambda x: None if pd.isna(x) else (x.date() if hasattr(x, 'date') else x))
                print(f"✅ Campo '{col}' preparado para date")
        
        # Converter campos de hora (já devem estar como time após extract_time_from_datetime)
        time_columns = ['inicio_hora', 'conclusao_prevista_hora']
        for col in time_columns:
            if col in df_processed.columns:
                # Garantir que valores None/NaT sejam None
                df_processed[col] = df_processed[col].apply(lambda x: None if pd.isna(x) else (x.time() if hasattr(x, 'time') else x))
                print(f"✅ Campo '{col}' preparado para time")
        
        print(f"\n✅ Processamento concluído. Linhas processadas: {len(df_processed)}")
        print("📊 Colunas finais:")
        for i, col in enumerate(df_processed.columns.tolist(), 1):
            print(f"   {i}. {col}")
        
        return df_processed
        
    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        return None

async def upsert_agenda_base_supabase(df, conn, table_name="agenda_base"):
    """
    Executa UPSERT na tabela agenda_base no Supabase.
    Baseado na função insert_data_to_supabase do rpa_agenda_rmb.py
    Chave: id_legalone
    """
    print(f"\n📊 Executando UPSERT na tabela '{table_name}' no Supabase...")
    print("="*70)
    
    try:
        # Verificar se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"❌ ERRO: Tabela '{table_name}' não existe!")
            return False
        
        print(f"✅ Tabela '{table_name}' encontrada!")
        
        # Contar registros antes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"📊 Registros existentes antes: {count_before}")
        
        # Obter colunas da tabela (exceto id e created_at que são automáticos)
        columns_info = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1
            AND column_name NOT IN ('id', 'created_at')
            ORDER BY ordinal_position
        """, table_name)
        
        table_columns = [row['column_name'] for row in columns_info]
        print(f"📋 Colunas da tabela: {len(table_columns)}")
        
        # Filtrar apenas colunas que existem no DataFrame e na tabela
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        if 'id_legalone' not in columns_df:
            print(f"❌ ERRO: Coluna 'id_legalone' não encontrada no DataFrame!")
            print(f"📋 Colunas disponíveis no DataFrame: {df.columns.tolist()}")
            return False
        
        print(f"✅ Colunas para processar: {len(columns_df)}")
        
        # Remover duplicatas baseado em id_legalone (manter o último)
        linhas_antes = len(df)
        df = df.drop_duplicates(subset=['id_legalone'], keep='last')
        linhas_depois = len(df)
        if linhas_antes != linhas_depois:
            print(f"⚠️ Removidas {linhas_antes - linhas_depois} duplicatas do DataFrame (mantido o último registro)")
        
        # Preparar query de INSERT (UPDATE será construído dinamicamente)
        columns_sql = ", ".join(f'"{col}"' for col in columns_df)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
        
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Processar em lotes para melhor performance
        batch_size = 100
        total_rows = len(df)
        
        print(f"\n🔄 Processando {total_rows} registros em lotes de {batch_size}...")
        
        # Processar em lotes menores para melhor controle de transações
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            async with conn.transaction():
                for index, row in batch_df.iterrows():
                    try:
                        id_legalone = row.get('id_legalone')
                        if not id_legalone or pd.isna(id_legalone):
                            skipped_count += 1
                            continue
                        
                        # Garantir que id_legalone seja int (converter de Int64 do pandas para int nativo)
                        if pd.isna(id_legalone):
                            skipped_count += 1
                            continue
                        
                        # Converter para int nativo do Python (não Int64 do pandas)
                        id_legalone = int(id_legalone) if not pd.isna(id_legalone) else None
                        if not id_legalone:
                            skipped_count += 1
                            continue
                        
                        # Método manual: verificar se existe e fazer UPDATE ou INSERT
                        exists = await conn.fetchval(
                            f"SELECT id_legalone FROM {table_name} WHERE id_legalone = $1",
                            id_legalone
                        )
                        
                        if exists:
                            # UPDATE - usar mesma abordagem do rpa_agenda_rmb.py
                            set_clauses = []
                            values = []
                            
                            for col in columns_df:
                                if col != 'id_legalone':  # Não incluir id_legalone no SET
                                    set_clauses.append(f'"{col}" = ${len(values) + 1}')
                                    values.append(clean_value_for_db(row[col]))
                            
                            values.append(id_legalone)  # Adicionar id_legalone para WHERE
                            
                            update_query_final = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id_legalone = ${len(values)}"
                            await conn.execute(update_query_final, *values)
                            updated_count += 1
                        else:
                            # INSERT - usar mesma abordagem do rpa_agenda_rmb.py
                            # Criar um Series apenas com as colunas necessárias na ordem correta
                            row_values = [row[col] for col in columns_df]
                            cleaned_values = tuple(clean_value_for_db(v) for v in row_values)
                            await conn.execute(insert_query, *cleaned_values)
                            inserted_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"⚠️ Erro ao processar linha {index + 1} (id_legalone={id_legalone}): {e}")
                        # Continuar com próximo registro mesmo em caso de erro
                        continue
                
                # Mostrar progresso
                progress = (batch_end / total_rows) * 100
                print(f"📊 Progresso: {batch_end}/{total_rows} ({progress:.1f}%) | "
                      f"Inseridos: {inserted_count} | Atualizados: {updated_count} | "
                      f"Pulados: {skipped_count} | Erros: {error_count}")
        
        # Verificar resultado
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        
        print(f"\n✅ UPSERT concluído!")
        print(f"📊 Registros inseridos: {inserted_count}")
        print(f"📊 Registros atualizados: {updated_count}")
        print(f"📊 Registros pulados: {skipped_count}")
        print(f"📊 Erros: {error_count}")
        print(f"📊 Total na tabela: {count_before} → {count_after}")
        
        # Verificar se atingiu o número esperado
        if count_after == 7209:
            print(f"\n✅ SUCESSO! Tabela contém exatamente 7209 registros!")
        else:
            print(f"\n⚠️ ATENÇÃO: Tabela contém {count_after} registros (esperado: 7209)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar UPSERT: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Função principal"""
    print("="*70)
    print("🔄 ATUALIZAÇÃO DA TABELA AGENDA_BASE")
    print("="*70)
    
    # 1. Carregar arquivo
    print("\n📂 ETAPA 1: Carregar arquivo Excel da pasta Downloads")
    print("="*70)
    downloads_dir = Path.home() / "Downloads"
    arquivo_path = downloads_dir / "atualizar_Agenda_1612.xlsx"
    
    if not arquivo_path.exists():
        print(f"❌ Erro: Arquivo não encontrado em {arquivo_path}")
        print(f"📋 Procurando arquivos similares na pasta Downloads...")
        if downloads_dir.exists():
            arquivos_xlsx = [f for f in downloads_dir.iterdir() if f.is_file() and f.suffix == '.xlsx' and 'agenda' in f.name.lower()]
            if arquivos_xlsx:
                print(f"     Arquivos encontrados:")
                for arquivo in arquivos_xlsx:
                    print(f"       - {arquivo.name}")
        return
    
    # 2. Processar dados
    print("\n🔄 ETAPA 2: Processar dados")
    print("="*70)
    df_processed = process_excel_file(str(arquivo_path))
    if df_processed is None or df_processed.empty:
        print("\n❌ Não foi possível processar os dados.")
        return
    
    # 3. Conectar ao Supabase
    print("\n🔗 ETAPA 3: Conectar ao Supabase")
    print("="*70)
    
    # Obter credenciais do .env
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "L7CEsmTv@vZKfpN")
    
    conn_supabase = None
    try:
        conn_supabase = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            ssl="require",
            statement_cache_size=0  # Desabilita prepared statements para pgbouncer
        )
        print("✅ Conexão estabelecida com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Supabase: {e}")
        import traceback
        traceback.print_exc()
        conn_supabase = None
    
    # 4. Executar UPSERT no Supabase
    if conn_supabase:
        print("\n📊 ETAPA 4: Executar UPSERT na tabela agenda_base (Supabase)")
        print("="*70)
        upsert_success_supabase = await upsert_agenda_base_supabase(df_processed, conn_supabase, "agenda_base")
        
        if upsert_success_supabase:
            print("\n✅ UPSERT no Supabase concluído com sucesso!")
        else:
            print("\n❌ ERRO: Falha ao executar UPSERT no Supabase")
        
        await conn_supabase.close()
        print("\n🔌 Conexão com Supabase fechada.")
    
    # 5. Executar UPSERT no MySQL Hostinger (datas tratadas no helper)
    print("\n📊 ETAPA 5: Executar UPSERT na tabela agenda_base (MySQL Hostinger)")
    print("="*70)
    upsert_success_hostinger = upsert_agenda_base_hostinger(df_processed, "agenda_base", "id_legalone")
    
    if upsert_success_hostinger:
        print("\n✅ UPSERT no MySQL Hostinger concluído com sucesso!")
    else:
        print("\n❌ ERRO: Falha ao executar UPSERT no MySQL Hostinger")
    
    # Resumo final
    print("\n" + "="*70)
    if conn_supabase and upsert_success_supabase and upsert_success_hostinger:
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("✅ UPSERT realizado no Supabase e no MySQL Hostinger")
    elif conn_supabase and upsert_success_supabase:
        print("⚠️ PROCESSO PARCIALMENTE CONCLUÍDO")
        print("✅ UPSERT realizado no Supabase")
        print("❌ UPSERT falhou no MySQL Hostinger")
    elif upsert_success_hostinger:
        print("⚠️ PROCESSO PARCIALMENTE CONCLUÍDO")
        print("❌ UPSERT falhou no Supabase")
        print("✅ UPSERT realizado no MySQL Hostinger")
    else:
        print("❌ ERRO: Falha ao executar UPSERT em ambos os bancos")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
