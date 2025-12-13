"""
Script para importar dados de andamentos do Excel para Azure SQL Database
Arquivo: atualiza_andamentos_1212.xlsx (na pasta Downloads)
Tabela: andamento_base (PK: id_andamento_legalone)
Usa UPSERT para evitar duplicatas
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

def processar_dataframe_andamentos(df):
    """
    Processa o DataFrame de andamentos, tratando tipos de dados
    """
    print("\n[INFO] Processando DataFrame...")
    
    # Converter id_agenda_legalone e id_andamento_legalone para Int64 (suporta nulos)
    if 'id_agenda_legalone' in df.columns:
        df['id_agenda_legalone'] = pd.to_numeric(df['id_agenda_legalone'], errors='coerce').astype('Int64')
    
    if 'id_andamento_legalone' in df.columns:
        df['id_andamento_legalone'] = pd.to_numeric(df['id_andamento_legalone'], errors='coerce').astype('Int64')
    
    # Processar cadastro_andamento: apenas data (desprezar hora)
    if 'cadastro_andamento' in df.columns:
        df['cadastro_andamento'] = pd.to_datetime(df['cadastro_andamento'], errors='coerce').dt.date
        print("[OK] Campo 'cadastro_andamento' processado -> apenas data (hora desprezada)")
    
    # Converter campos de texto (substituir NaN por None)
    text_columns = ['tipo_andamento', 'subtipo_andamento', 'descricao_andamento']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].replace({pd.NA: None, 'nan': None, 'None': None, '': None})
    
    print(f"[OK] DataFrame processado: {len(df)} registros")
    print(f"[INFO] Colunas finais: {df.columns.tolist()}")
    return df

def insert_andamentos_to_azure(df, table_name="andamento_base"):
    """
    Insere/atualiza dados na tabela andamento_base no Azure SQL Database
    Usa UPSERT baseado em id_andamento_legalone (PK)
    """
    print(f"\n{'='*80}")
    print(f"[UPSERT] PROCESSANDO ANDAMENTOS - UPSERT NO AZURE")
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
        
        # Carregar IDs de agenda_base para validar FK
        print(f"\n[INFO] Carregando IDs validos da tabela agenda_base...")
        cursor.execute("SELECT id_legalone FROM agenda_base")
        valid_agenda_ids = set(row[0] for row in cursor.fetchall())
        print(f"[OK] {len(valid_agenda_ids)} IDs validos carregados")
        
        # Filtrar DataFrame: apenas andamentos com id_agenda_legalone válido
        linhas_antes_fk = len(df)
        if 'id_agenda_legalone' in df.columns:
            df = df[df['id_agenda_legalone'].isin(valid_agenda_ids)]
            linhas_depois_fk = len(df)
            removidos_fk = linhas_antes_fk - linhas_depois_fk
            if removidos_fk > 0:
                print(f"[AVISO] Removidos {removidos_fk} registros com id_agenda_legalone invalido (nao existe em agenda_base)")
        
        # Obter colunas da tabela no Azure
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? 
            ORDER BY ORDINAL_POSITION
        """, table_name)
        table_columns = [row[0] for row in cursor.fetchall()]
        
        # Filtrar apenas colunas que existem na tabela e no DataFrame
        columns_df = [col for col in df.columns.tolist() if col in table_columns]
        
        # Verificar se id_andamento_legalone está presente (obrigatório como PK)
        if 'id_andamento_legalone' not in columns_df:
            print("[ERRO] Coluna 'id_andamento_legalone' nao encontrada!")
            return False
        
        print(f"[INFO] Colunas que serao inseridas: {columns_df}")
        
        # Remover duplicatas no DataFrame (manter o último)
        print(f"\n[INFO] Verificando duplicatas no DataFrame...")
        linhas_antes = len(df)
        df = df.drop_duplicates(subset=['id_andamento_legalone'], keep='last')
        linhas_depois = len(df)
        if linhas_antes != linhas_depois:
            print(f"[AVISO] Removidas {linhas_antes - linhas_depois} duplicatas do DataFrame (mantido o ultimo registro)")
        
        # Processar em lotes para melhor performance
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        batch_size = 100
        total_rows = len(df)
        
        print(f"\n[INFO] Processando {total_rows} registros em lotes de {batch_size}...")
        print(f"[INFO] Usando UPSERT (UPDATE se existe, INSERT se nao existe)...")
        
        # Preparar queries
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        # Query para verificar se existe
        check_query = f"SELECT COUNT(*) FROM {table_name} WHERE id_andamento_legalone = ?"
        
        # Query para UPDATE (todos os campos exceto id_andamento_legalone)
        update_columns = [col for col in columns_df if col != 'id_andamento_legalone']
        set_clauses = ", ".join(f"[{col}] = ?" for col in update_columns)
        update_query = f"UPDATE {table_name} SET {set_clauses} WHERE id_andamento_legalone = ?"
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            for index, row in batch_df.iterrows():
                id_andamento_legalone = row.get('id_andamento_legalone')
                
                # Pular se id_andamento_legalone estiver vazio (obrigatório como PK)
                if not id_andamento_legalone or pd.isna(id_andamento_legalone):
                    skipped_count += 1
                    continue
                
                # Verificar se já existe
                cursor.execute(check_query, (id_andamento_legalone,))
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
                    update_values = [v for col, v in zip(columns_df, values) if col != 'id_andamento_legalone']
                    update_values.append(id_andamento_legalone)
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
        print(f"   Pulados (sem id_andamento_legalone): {skipped_count}")
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

def buscar_arquivos_andamentos():
    """Busca os arquivos de andamentos divididos (1, 2, 3)"""
    base_name = "atualiza_andamentos_1212"
    possible_dirs = [
        os.path.join(os.path.expanduser("~"), "Downloads"),  # Downloads do Windows
        os.path.join("downloads"),  # downloads/ do projeto
        os.path.join("Downloads"),  # Caminho relativo
        "."  # Diretório atual
    ]
    
    arquivos_encontrados = []
    
    for diretorio in possible_dirs:
        for sufixo in ["_1", "_2", "_3", ""]:  # Tentar com sufixo e sem sufixo
            nome_arquivo = f"{base_name}{sufixo}.xlsx"
            caminho_completo = os.path.join(diretorio, nome_arquivo)
            if os.path.exists(caminho_completo):
                if caminho_completo not in arquivos_encontrados:
                    arquivos_encontrados.append(caminho_completo)
    
    # Ordenar para processar na ordem (1, 2, 3)
    arquivos_encontrados.sort()
    
    return arquivos_encontrados

def main():
    """Função principal"""
    print("=" * 80)
    print("[IMPORTAR] IMPORTAR ANDAMENTOS PARA AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Buscar arquivos
    arquivos = buscar_arquivos_andamentos()
    
    if not arquivos:
        print(f"[ERRO] Nenhum arquivo encontrado!")
        print(f"   Procurando por: atualiza_andamentos_1212_1.xlsx, atualiza_andamentos_1212_2.xlsx, atualiza_andamentos_1212_3.xlsx")
        print(f"   Ou: atualiza_andamentos_1212.xlsx")
        return
    
    print(f"[OK] {len(arquivos)} arquivo(s) encontrado(s):")
    for arquivo in arquivos:
        print(f"   - {arquivo}")
    print()
    
    total_inseridos = 0
    total_atualizados = 0
    total_pulados = 0
    
    # Processar cada arquivo
    for idx, file_andamentos in enumerate(arquivos, 1):
        print("\n" + "=" * 80)
        print(f"[ARQUIVO {idx}/{len(arquivos)}] Processando: {os.path.basename(file_andamentos)}")
        print("=" * 80)
        
        try:
            # Ler o arquivo Excel
            print(f"\n[INFO] Lendo arquivo: {file_andamentos}")
            df_andamentos = pd.read_excel(file_andamentos)
            print(f"[OK] Arquivo lido: {len(df_andamentos)} linhas")
            print(f"[INFO] Colunas encontradas: {df_andamentos.columns.tolist()}")
            
            # Processar DataFrame
            df_processed = processar_dataframe_andamentos(df_andamentos)
            
            # Importar para Azure SQL Database
            success = insert_andamentos_to_azure(df_processed, "andamento_base")
            
            if success:
                print(f"\n[OK] Arquivo {idx} processado com sucesso!")
            else:
                print(f"\n[ERRO] Erro ao processar arquivo {idx}")
                break
                
        except Exception as e:
            print(f"\n[ERRO] Erro ao processar arquivo {file_andamentos}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("[RESUMO] PROCESSAMENTO CONCLUIDO")
    print("=" * 80)
    print(f"   Arquivos processados: {len(arquivos)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
