"""
Script para importar dados da agenda do Excel para Azure SQL Database
Arquivo: atualiza_agenda_1212.xlsx (na pasta Downloads)
Tabela: agenda_base (PK: id_legalone)
Filtro: executante_sim = 'Sim'
"""

import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('config.env')

def get_azure_connection():
    """
    Conecta ao Azure SQL Database
    """
    # Configurações do Azure (lidas do config.env)
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    # Validar se as variáveis obrigatórias foram configuradas
    if not server or not database or not username or not password:
        print("\n[ERRO] Configuracoes incompletas no config.env!")
        print("   Configure as variaveis AZURE_*")
        return None
    
    # Tentar diferentes drivers ODBC
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
        "SQL Server Native Client 11.0"
    ]
    
    available_drivers = pyodbc.drivers()
    
    # Encontrar um driver disponível
    driver = None
    for drv in drivers_to_try:
        if drv in available_drivers:
            driver = drv
            break
    
    if not driver:
        print(f"\n[ERRO] Nenhum driver ODBC para SQL Server encontrado!")
        return None
    
    # String de conexão para Azure SQL Database
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(connection_string, timeout=30)
        print(f"[OK] Conectado ao Azure SQL Database: {server}:{port}/{database}")
        return conn
    except Exception as e:
        print(f"\n[ERRO] Erro ao conectar ao Azure SQL Database: {e}")
        return None

def processar_dataframe_agenda(df):
    """
    Processa o DataFrame da agenda, separando data/hora e aplicando filtro
    """
    print("\n[INFO] Processando DataFrame...")
    
    # Converter id_legalone para Int64 (suporta nulos)
    if 'id_legalone' in df.columns:
        df['id_legalone'] = pd.to_numeric(df['id_legalone'], errors='coerce').astype('Int64')
    
    # Separar colunas de data/hora combinadas
    # Excel: 'inicio' (datetime) -> SQL: 'inicio_data' (date) + 'inicio_hora' (time)
    if 'inicio' in df.columns:
        df['inicio'] = pd.to_datetime(df['inicio'], errors='coerce')
        df['inicio_data'] = df['inicio'].dt.date
        df['inicio_hora'] = df['inicio'].dt.time
        df = df.drop(columns=['inicio'])
    
    if 'conclusao_prevista' in df.columns:
        df['conclusao_prevista'] = pd.to_datetime(df['conclusao_prevista'], errors='coerce')
        df['conclusao_prevista_data'] = df['conclusao_prevista'].dt.date
        df['conclusao_prevista_hora'] = df['conclusao_prevista'].dt.time
        df = df.drop(columns=['conclusao_prevista'])
    
    # conclusao_efetiva é apenas data (sem hora na tabela)
    if 'conclusao_efetiva' in df.columns:
        df['conclusao_efetiva'] = pd.to_datetime(df['conclusao_efetiva'], errors='coerce')
        df['conclusao_efetiva_data'] = df['conclusao_efetiva'].dt.date
        df = df.drop(columns=['conclusao_efetiva'])
    
    # prazo_fatal é apenas data
    if 'prazo_fatal' in df.columns:
        df['prazo_fatal'] = pd.to_datetime(df['prazo_fatal'], errors='coerce')
        df['prazo_fatal_data'] = df['prazo_fatal'].dt.date
        df = df.drop(columns=['prazo_fatal'])
    
    # cadastro é apenas data
    if 'cadastro' in df.columns:
        df['cadastro'] = pd.to_datetime(df['cadastro'], errors='coerce').dt.date
    
    # Renomear Pasta_proc para pasta_proc (case sensitive)
    if 'Pasta_proc' in df.columns:
        df = df.rename(columns={'Pasta_proc': 'pasta_proc'})
    
    # FILTRAR: Apenas registros onde executante_sim = "Sim"
    print("\n[FILTRO] Aplicando filtro: executante_sim = 'Sim'...")
    if 'executante_sim' in df.columns:
        linhas_antes = len(df)
        # Filtrar (case-insensitive para garantir)
        df = df[df['executante_sim'].astype(str).str.strip().str.capitalize() == 'Sim']
        linhas_depois = len(df)
        print(f"[OK] Filtro aplicado: {linhas_antes} -> {linhas_depois} linhas")
        print(f"[INFO] Removidas {linhas_antes - linhas_depois} linhas com executante_sim != 'Sim'")
    else:
        print("[AVISO] Coluna 'executante_sim' nao encontrada, pulando filtro")
    
    # Converter campos de texto (substituir NaN por None)
    text_columns = ['compromisso_tarefa', 'tipo', 'subtipo', 'etiqueta', 
                    'pasta_proc', 'numero_cnj', 'executante', 'executante_sim',
                    'descricao', 'status', 'link']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].replace({pd.NA: None, 'nan': None, 'None': None, '': None})
    
    print(f"[OK] DataFrame processado: {len(df)} registros")
    print(f"[INFO] Colunas finais: {df.columns.tolist()}")
    return df

def insert_agenda_to_azure(df, table_name="agenda_base"):
    """
    Insere dados na tabela agenda_base no Azure SQL Database
    Como a tabela está vazia, usa apenas INSERT
    PK: id_legalone
    """
    print(f"\n{'='*80}")
    print(f"[INSERT] PROCESSANDO AGENDA - INSERT NO AZURE")
    print(f"{'='*80}")
    
    # Conectar ao Azure
    conn = get_azure_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ?
        """, table_name)
        if cursor.fetchone()[0] == 0:
            print(f"[ERRO] Tabela '{table_name}' nao existe!")
            return False
        
        # Contar registros antes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_before = cursor.fetchone()[0]
        print(f"[INFO] Registros existentes: {count_before}")
        
        # Obter colunas da tabela no Azure
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? 
            AND COLUMN_NAME NOT IN ('created_at')
            ORDER BY ORDINAL_POSITION
        """, table_name)
        table_columns = [row[0] for row in cursor.fetchall()]
        
        # Filtrar apenas colunas que existem na tabela e no DataFrame
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        # Garantir que id_legalone está presente (é obrigatório como PK)
        if 'id_legalone' not in columns_df:
            print("[ERRO] Coluna 'id_legalone' nao encontrada!")
            return False
        
        print(f"[INFO] Colunas que serao inseridas: {columns_df}")
        
        # Remover duplicatas no DataFrame (manter o último)
        print(f"\n[INFO] Verificando duplicatas no DataFrame...")
        linhas_antes = len(df)
        df = df.drop_duplicates(subset=['id_legalone'], keep='last')
        linhas_depois = len(df)
        if linhas_antes != linhas_depois:
            print(f"[AVISO] Removidas {linhas_antes - linhas_depois} duplicatas do DataFrame (mantido o ultimo registro)")
        
        # Processar em lotes para melhor performance
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        duplicate_count = 0
        batch_size = 100
        total_rows = len(df)
        
        print(f"\n[INFO] Processando {total_rows} registros em lotes de {batch_size}...")
        print(f"[INFO] Usando UPSERT (UPDATE se existe, INSERT se nao existe)...")
        
        # Preparar queries
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        # Query para verificar se existe
        check_query = f"SELECT COUNT(*) FROM {table_name} WHERE id_legalone = ?"
        
        # Query para UPDATE (todos os campos exceto id_legalone)
        update_columns = [col for col in columns_df if col != 'id_legalone']
        set_clauses = ", ".join(f"[{col}] = ?" for col in update_columns)
        update_query = f"UPDATE {table_name} SET {set_clauses} WHERE id_legalone = ?"
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            for index, row in batch_df.iterrows():
                id_legalone = row.get('id_legalone')
                
                # Pular se id_legalone estiver vazio (obrigatório como PK)
                if not id_legalone or pd.isna(id_legalone):
                    skipped_count += 1
                    continue
                
                # Verificar se já existe
                cursor.execute(check_query, (id_legalone,))
                exists = cursor.fetchone()[0] > 0
                
                # Preparar valores (converter NaN para None)
                values = []
                for col in columns_df:
                    value = row[col]
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                
                if exists:
                    # UPDATE
                    update_values = [v for col, v in zip(columns_df, values) if col != 'id_legalone']
                    update_values.append(id_legalone)
                    cursor.execute(update_query, update_values)
                    updated_count += 1
                else:
                    # INSERT
                    cursor.execute(insert_query, values)
                    inserted_count += 1
            
            # Commit a cada lote
            conn.commit()
            
            # Mostrar progresso
            progress = (batch_end / total_rows) * 100
            print(f"[PROGRESSO] {batch_end}/{total_rows} ({progress:.1f}%) | "
                  f"Inseridos: {inserted_count} | Atualizados: {updated_count} | Pulados: {skipped_count}")
        
        # Commit final (caso necessário)
        conn.commit()
        
        # Contar após
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_after = cursor.fetchone()[0]
        
        print(f"\n[OK] UPSERT CONCLUIDO!")
        print(f"   Inseridos: {inserted_count}")
        print(f"   Atualizados: {updated_count}")
        print(f"   Pulados (sem id_legalone): {skipped_count}")
        print(f"   Total na tabela: {count_before} -> {count_after}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Função principal"""
    print("=" * 80)
    print("[IMPORTAR] IMPORTAR AGENDA PARA AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Tentar múltiplos caminhos para o arquivo
    possible_paths = [
        os.path.join("downloads", "atualiza_agenda_1212.xlsx"),  # downloads/ do projeto
        os.path.join(os.path.expanduser("~"), "Downloads", "atualiza_agenda_1212.xlsx"),  # Downloads do Windows
        os.path.join("Downloads", "atualiza_agenda_1212.xlsx"),  # Caminho relativo
        "atualiza_agenda_1212.xlsx"  # Diretório atual
    ]
    
    file_agenda = None
    for path in possible_paths:
        if os.path.exists(path):
            file_agenda = path
            print(f"[OK] Arquivo encontrado em: {path}")
            break
    
    if not file_agenda:
        print(f"[ERRO] Arquivo nao encontrado: atualiza_agenda_1212.xlsx")
        print(f"   Procurando em:")
        for path in possible_paths:
            print(f"   - {path}")
        return
    
    try:
        # Ler o arquivo Excel
        print(f"\n[INFO] Lendo arquivo: {file_agenda}")
        df_agenda = pd.read_excel(file_agenda)
        print(f"[OK] Arquivo lido: {len(df_agenda)} linhas")
        print(f"[INFO] Colunas encontradas: {df_agenda.columns.tolist()}")
        
        # Processar DataFrame
        df_processed = processar_dataframe_agenda(df_agenda)
        
        # Importar para Azure SQL Database
        success = insert_agenda_to_azure(df_processed, "agenda_base")
        
        if success:
            print("\n" + "=" * 80)
            print("[SUCESSO] AGENDA IMPORTADA COM SUCESSO PARA AZURE!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("[ERRO] ERRO AO IMPORTAR AGENDA")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n[ERRO] Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

