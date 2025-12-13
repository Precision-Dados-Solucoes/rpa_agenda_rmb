import pandas as pd
import os
import asyncio
import asyncpg
from pathlib import Path
from dotenv import load_dotenv
from azure_sql_helper import insert_publicacoes

load_dotenv()

def carregar_arquivo_publicacoes():
    """
    Carrega o arquivo z-rpa-publicacoes (2).xlsx ou z-rpa-publicacoes.xlsx.
    Procura primeiro no diretório atual, depois na pasta Downloads.
    """
    # Lista de possíveis nomes de arquivo (em ordem de prioridade)
    nomes_arquivo = [
        "z-rpa-publicacoes (2).xlsx",
        "z-rpa-publicacoes.xlsx"
    ]
    
    # Lista de diretórios para procurar
    diretorios = [
        Path.cwd(),  # Diretório atual
        Path.home() / "Downloads"  # Pasta Downloads
    ]
    
    arquivo_path = None
    
    # Procurar o arquivo
    for diretorio in diretorios:
        for nome_arquivo in nomes_arquivo:
            caminho_teste = diretorio / nome_arquivo
            if caminho_teste.exists():
                arquivo_path = caminho_teste
                print(f"📂 Arquivo encontrado: {arquivo_path}")
                break
        if arquivo_path:
            break
    
    # Se não encontrou, listar arquivos disponíveis
    if not arquivo_path:
        print(f"❌ Erro: Arquivo não encontrado!")
        print(f"📋 Procurando em:")
        for diretorio in diretorios:
            if diretorio.exists():
                print(f"   - {diretorio}")
                arquivos_xlsx = [f for f in diretorio.iterdir() if f.is_file() and f.suffix == '.xlsx' and 'publicacoes' in f.name.lower()]
                if arquivos_xlsx:
                    print(f"     Arquivos encontrados:")
                    for arquivo in arquivos_xlsx:
                        print(f"       - {arquivo.name}")
        return None
    
    try:
        # Carregar o arquivo Excel
        print(f"🔄 Carregando arquivo Excel...")
        df = pd.read_excel(arquivo_path)
        
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"📊 Total de linhas: {len(df)}")
        print(f"📊 Total de colunas: {len(df.columns)}")
        print(f"\n📋 Colunas do DataFrame:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        return df
    
    except Exception as e:
        print(f"❌ Erro ao carregar o arquivo Excel: {e}")
        return None

def processar_dados(df):
    """
    Processa os dados do DataFrame, separando data/hora das colunas datetime.
    """
    print("\n🔄 Processando dados...")
    print("="*70)
    
    # Criar novo DataFrame processado
    df_processed = pd.DataFrame()
    
    # Separar "Data/hora cadastro" em data_cadastro e hora_cadastro
    if 'Data/hora cadastro' in df.columns:
        print("📅 Processando coluna 'Data/hora cadastro'...")
        df_processed['data_cadastro'] = df['Data/hora cadastro'].apply(lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None)
        df_processed['hora_cadastro'] = df['Data/hora cadastro'].apply(lambda x: x.time() if pd.notna(x) and hasattr(x, 'time') else None)
        print("✅ 'Data/hora cadastro' → 'data_cadastro' e 'hora_cadastro'")
    else:
        print("⚠️ Coluna 'Data/hora cadastro' não encontrada")
        df_processed['data_cadastro'] = None
        df_processed['hora_cadastro'] = None
    
    # Separar "Data/hora" em data_publicacao e hora_publicacao
    if 'Data/hora' in df.columns:
        print("📅 Processando coluna 'Data/hora'...")
        df_processed['data_publicacao'] = df['Data/hora'].apply(lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None)
        df_processed['hora_publicacao'] = df['Data/hora'].apply(lambda x: x.time() if pd.notna(x) and hasattr(x, 'time') else None)
        print("✅ 'Data/hora' → 'data_publicacao' e 'hora_publicacao'")
    else:
        print("⚠️ Coluna 'Data/hora' não encontrada")
        df_processed['data_publicacao'] = None
        df_processed['hora_publicacao'] = None
    
    # Copiar colunas restantes
    colunas_restantes = {
        'Pasta': 'pasta',
        'Número de CNJ': 'numero_cnj',
        'Tratamento': 'tratamento',
        'Publicação': 'publicacao'
    }
    
    for col_original, col_nova in colunas_restantes.items():
        if col_original in df.columns:
            df_processed[col_nova] = df[col_original]
            print(f"✅ '{col_original}' → '{col_nova}'")
        else:
            print(f"⚠️ Coluna '{col_original}' não encontrada")
            df_processed[col_nova] = None
    
    print(f"\n✅ Processamento concluído!")
    print(f"📊 Total de registros processados: {len(df_processed)}")
    
    return df_processed

async def inserir_dados_supabase(df, table_name="tb_publicacoes"):
    """
    Insere os dados processados na tabela do Supabase.
    """
    print(f"\n🔗 Conectando ao Supabase...")
    print("="*70)
    
    # Obter credenciais do .env ou usar valores padrão
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Tentar construir a connection string a partir de variáveis individuais
        host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
        port = os.getenv("SUPABASE_PORT", "5432")
        database = os.getenv("SUPABASE_DATABASE", "postgres")
        user = os.getenv("SUPABASE_USER", "postgres")
        password = os.getenv("SUPABASE_PASSWORD", "L7CEsmTv@vZKfpN")
        
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=int(port),
                database=database,
                ssl="require"
            )
        except Exception as e:
            print(f"❌ Erro ao conectar com credenciais individuais: {e}")
            return False
    else:
        try:
            conn = await asyncpg.connect(database_url)
        except Exception as e:
            print(f"❌ Erro ao conectar com connection string: {e}")
            return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
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
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"📊 Registros existentes: {count_before}")
        
        # Preparar colunas para inserção
        columns_df = df.columns.tolist()
        columns_sql = ", ".join(f'"{col}"' for col in columns_df)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        print(f"\n📊 Inserindo {len(df)} registros...")
        print("="*70)
        
        inserted_count = 0
        
        async with conn.transaction():
            for index, row in df.iterrows():
                try:
                    # Preparar valores
                    values = []
                    for col in columns_df:
                        value = row[col]
                        # Tratar valores NaN/None
                        if pd.isna(value):
                            values.append(None)
                        else:
                            values.append(value)
                    
                    # Inserir registro
                    await conn.execute(insert_query, *values)
                    inserted_count += 1
                    
                    if (index + 1) % 10 == 0:
                        print(f"✅ {inserted_count} registros inseridos...")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao inserir linha {index + 1}: {e}")
                    continue
        
        # Verificar resultado
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"\n✅ Inserção concluída!")
        print(f"📊 Registros inseridos: {inserted_count}")
        print(f"📊 Total na tabela: {count_before} → {count_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()
        print("🔌 Conexão fechada.")

async def main():
    """Função principal"""
    print("="*70)
    print("🚀 Processando e inserindo publicações no Supabase")
    print("="*70)
    
    # 1. Carregar arquivo
    df = carregar_arquivo_publicacoes()
    if df is None:
        print("\n❌ Não foi possível carregar o arquivo.")
        return
    
    # 2. Processar dados
    df_processed = processar_dados(df)
    
    # 3. Inserir no Supabase
    sucesso = await inserir_dados_supabase(df_processed)
    
    if sucesso:
        print("\n✅ Processo concluído com sucesso!")
    else:
        print("\n❌ Erro ao inserir dados no Supabase")

if __name__ == "__main__":
    asyncio.run(main())

