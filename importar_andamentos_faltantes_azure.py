"""
Script para importar apenas os andamentos que faltam na tabela
Compara id_andamento_legalone do arquivo com os que já existem na tabela
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
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    username = os.getenv("AZURE_USER")
    password = os.getenv("AZURE_PASSWORD")
    port = os.getenv("AZURE_PORT", "1433")
    
    if not server or not database or not username or not password:
        print("\n[ERRO] Configuracoes incompletas no config.env!")
        return None
    
    drivers_to_try = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server",
        "SQL Server Native Client 11.0"
    ]
    
    available_drivers = pyodbc.drivers()
    
    driver = None
    for drv in drivers_to_try:
        if drv in available_drivers:
            driver = drv
            break
    
    if not driver:
        print(f"\n[ERRO] Nenhum driver ODBC para SQL Server encontrado!")
        return None
    
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
    return df

def main():
    """Função principal"""
    print("=" * 80)
    print("[IMPORTAR] IMPORTAR APENAS ANDAMENTOS FALTANTES - AZURE SQL DATABASE")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Buscar arquivo
    possible_paths = [
        os.path.join(os.path.expanduser("~"), "Downloads", "atualiza_andamentos_1212.xlsx"),
        os.path.join("downloads", "atualiza_andamentos_1212.xlsx"),
        os.path.join("Downloads", "atualiza_andamentos_1212.xlsx"),
        "atualiza_andamentos_1212.xlsx"
    ]
    
    file_andamentos = None
    for path in possible_paths:
        if os.path.exists(path):
            file_andamentos = path
            print(f"[OK] Arquivo encontrado em: {path}")
            break
    
    if not file_andamentos:
        print(f"[ERRO] Arquivo nao encontrado: atualiza_andamentos_1212.xlsx")
        return
    
    # Conectar ao Azure
    conn = get_azure_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Carregar IDs que já existem na tabela
        print(f"\n[INFO] Carregando IDs que ja existem na tabela andamento_base...")
        cursor.execute("SELECT id_andamento_legalone FROM andamento_base")
        existing_ids = set(row[0] for row in cursor.fetchall())
        print(f"[OK] {len(existing_ids)} IDs encontrados na tabela")
        
        # 2. Carregar IDs válidos da agenda_base (para validar FK)
        print(f"\n[INFO] Carregando IDs validos da tabela agenda_base...")
        cursor.execute("SELECT id_legalone FROM agenda_base")
        valid_agenda_ids = set(row[0] for row in cursor.fetchall())
        print(f"[OK] {len(valid_agenda_ids)} IDs validos carregados")
        
        # 3. Ler arquivo Excel
        print(f"\n[INFO] Lendo arquivo: {file_andamentos}")
        df = pd.read_excel(file_andamentos)
        print(f"[OK] Arquivo lido: {len(df)} linhas")
        
        # 4. Processar DataFrame
        df_processed = processar_dataframe_andamentos(df)
        
        # 5. Filtrar apenas andamentos que NÃO estão na tabela
        print(f"\n[INFO] Filtrando andamentos que NAO estao na tabela...")
        linhas_antes = len(df_processed)
        
        # Remover duplicatas no DataFrame primeiro
        duplicatas_antes = len(df_processed)
        df_processed = df_processed.drop_duplicates(subset=['id_andamento_legalone'], keep='last')
        duplicatas_removidas = duplicatas_antes - len(df_processed)
        if duplicatas_removidas > 0:
            print(f"[INFO] Removidas {duplicatas_removidas} duplicatas do DataFrame")
        
        # Filtrar: apenas os que não existem na tabela
        linhas_antes_filtro = len(df_processed)
        df_nao_existem = df_processed[~df_processed['id_andamento_legalone'].isin(existing_ids)]
        removidos_existentes = linhas_antes_filtro - len(df_nao_existem)
        print(f"[INFO] Removidos {removidos_existentes} andamentos que ja existem na tabela")
        
        # Separar por FK válida/inválida
        df_fk_valida = df_nao_existem[df_nao_existem['id_agenda_legalone'].isin(valid_agenda_ids)]
        df_fk_invalida = df_nao_existem[~df_nao_existem['id_agenda_legalone'].isin(valid_agenda_ids)]
        
        print(f"[INFO] Andamentos com FK valida: {len(df_fk_valida)}")
        print(f"[INFO] Andamentos com FK invalida: {len(df_fk_invalida)}")
        
        # Incluir TODOS os que não estão na tabela (mesmo com FK inválida)
        # O usuário pediu para incluir os que não estão na tabela
        df_processed = df_nao_existem.copy()
        
        if len(df_fk_invalida) > 0:
            print(f"[AVISO] {len(df_fk_invalida)} andamentos tem id_agenda_legalone invalido")
            print(f"[AVISO] Eles serao inseridos mesmo assim (FK pode falhar se a constraint estiver ativa)")
        
        linhas_depois = len(df_processed)
        print(f"[OK] Filtro aplicado: {linhas_antes} -> {linhas_depois} linhas")
        print(f"[INFO] {linhas_depois} andamentos faltantes encontrados")
        
        if linhas_depois == 0:
            print("\n[INFO] Nenhum andamento faltante encontrado!")
            print(f"[INFO] Resumo:")
            print(f"   - Total no arquivo: {linhas_antes}")
            print(f"   - Duplicatas no arquivo: {duplicatas_removidas}")
            print(f"   - Ja existem na tabela: {removidos_existentes}")
            print(f"   - Com id_agenda_legalone invalido: {removidos_fk}")
            print(f"\n[INFO] Todos os andamentos validos do arquivo ja estao na tabela.")
            
            # Mostrar alguns exemplos dos que foram removidos por FK inválida
            if removidos_fk > 0:
                print(f"\n[INFO] Verificando os {removidos_fk} andamentos com id_agenda_legalone invalido...")
                df_fk_invalidos = df_nao_existem[~df_nao_existem['id_agenda_legalone'].isin(valid_agenda_ids)]
                if len(df_fk_invalidos) > 0:
                    print(f"[INFO] Exemplos de id_agenda_legalone invalidos (primeiros 10):")
                    exemplos = df_fk_invalidos['id_agenda_legalone'].head(10).tolist()
                    for ex in exemplos:
                        print(f"   - {ex}")
            
            return
        
        # 6. Obter colunas da tabela
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'andamento_base'
            ORDER BY ORDINAL_POSITION
        """)
        table_columns = [row[0] for row in cursor.fetchall()]
        columns_df = [col for col in df_processed.columns.tolist() if col in table_columns]
        
        print(f"\n[INFO] Colunas que serao inseridas: {columns_df}")
        
        # 7. Inserir apenas os faltantes
        print(f"\n[INFO] Inserindo {linhas_depois} andamentos faltantes...")
        
        columns_sql = ", ".join(f'[{col}]' for col in columns_df)
        placeholders = ", ".join(["?"] * len(columns_df))
        insert_query = f"INSERT INTO andamento_base ({columns_sql}) VALUES ({placeholders})"
        
        inserted_count = 0
        skipped_count = 0
        fk_error_count = 0
        batch_size = 100
        total_rows = len(df_processed)
        
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df_processed.iloc[batch_start:batch_end]
            
            for index, row in batch_df.iterrows():
                id_andamento_legalone = row.get('id_andamento_legalone')
                
                if not id_andamento_legalone or pd.isna(id_andamento_legalone):
                    skipped_count += 1
                    continue
                
                # Preparar valores
                values = []
                for col in columns_df:
                    value = row[col]
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                
                # INSERT (pode falhar se FK estiver ativa)
                try:
                    cursor.execute(insert_query, values)
                    inserted_count += 1
                except pyodbc.IntegrityError as e:
                    if "FOREIGN KEY" in str(e) or "FK_" in str(e):
                        fk_error_count += 1
                        print(f"[AVISO] FK error para id_andamento_legalone {id_andamento_legalone}: {str(e)[:100]}")
                    else:
                        raise
            
            # Commit a cada lote
            conn.commit()
            
            # Mostrar progresso
            progress = (batch_end / total_rows) * 100
            print(f"[PROGRESSO] {batch_end}/{total_rows} ({progress:.1f}%) | Inseridos: {inserted_count} | Pulados: {skipped_count} | FK Errors: {fk_error_count}")
        
        # Commit final
        conn.commit()
        
        # Contar após
        cursor.execute("SELECT COUNT(*) FROM andamento_base")
        count_after = cursor.fetchone()[0]
        
        print(f"\n[OK] INSERCAO CONCLUIDA!")
        print(f"   Inseridos: {inserted_count}")
        print(f"   Pulados: {skipped_count}")
        if fk_error_count > 0:
            print(f"   Erros de FK: {fk_error_count}")
        print(f"   Total na tabela: {count_after}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("[SUCESSO] ANDAMENTOS FALTANTES IMPORTADOS COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERRO] Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    main()

