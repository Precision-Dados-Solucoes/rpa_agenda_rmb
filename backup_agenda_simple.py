#!/usr/bin/env python3
"""
Script para fazer backup da tabela agenda_base antes da limpeza
Versão simplificada sem emojis para compatibilidade com Windows
"""

import asyncio
import asyncpg
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv('config.env')

async def connect_to_supabase():
    """Conecta ao Supabase"""
    try:
        # Credenciais do Supabase
        host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
        port = os.getenv("SUPABASE_PORT", "5432")
        database = os.getenv("SUPABASE_DATABASE", "postgres")
        user = os.getenv("SUPABASE_USER", "postgres")
        password = os.getenv("SUPABASE_PASSWORD", "**PDS2025@@")
        
        print(f"[CONNECT] Conectando ao Supabase: {host}:{port}/{database}")
        
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            ssl='require'
        )
        
        print("[OK] Conexão estabelecida com sucesso!")
        return conn
        
    except Exception as e:
        print(f"[ERRO] Erro ao conectar: {e}")
        return None

async def create_backup(conn):
    """Cria backup da tabela agenda_base"""
    print("\n[BACKUP] CRIANDO BACKUP DA TABELA AGENDA_BASE...")
    
    # Obter todos os dados da tabela
    query = "SELECT * FROM agenda_base ORDER BY id"
    records = await conn.fetch(query)
    
    if not records:
        print("[AVISO] Nenhum registro encontrado na tabela")
        return None
    
    # Converter para DataFrame
    df = pd.DataFrame([dict(record) for record in records])
    
    # Converter todas as colunas para string para evitar problemas com timezone
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    # Criar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_agenda_base_{timestamp}.xlsx"
    
    # Salvar como Excel
    df.to_excel(backup_filename, index=False)
    
    print(f"[OK] Backup criado: {backup_filename}")
    print(f"[INFO] Total de registros no backup: {len(df)}")
    
    # Mostrar estatísticas
    print(f"\n[STATS] ESTATISTICAS DO BACKUP:")
    print(f"  - Total de registros: {len(df)}")
    print(f"  - Colunas: {len(df.columns)}")
    
    # Contagem por status
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        print(f"  - Por status:")
        for status, count in status_counts.items():
            print(f"    * {status or 'NULL'}: {count}")
    
    # Verificar duplicados
    if 'id_legalone' in df.columns:
        duplicates = df['id_legalone'].value_counts()
        duplicates = duplicates[duplicates > 1]
        print(f"  - Duplicados por id_legalone: {len(duplicates)}")
        
        if len(duplicates) > 0:
            print(f"    * Total de registros duplicados: {duplicates.sum()}")
    
    return backup_filename

async def main():
    """Função principal"""
    print("BACKUP DA TABELA AGENDA_BASE")
    print("="*40)
    
    # Conectar ao banco
    conn = await connect_to_supabase()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco")
        return
    
    try:
        backup_file = await create_backup(conn)
        
        if backup_file:
            print(f"\n[SUCCESS] BACKUP CONCLUIDO COM SUCESSO!")
            print(f"[FILE] Arquivo: {backup_file}")
            print(f"[INFO] Use este backup para restaurar dados se necessário")
        else:
            print("[ERRO] Falha ao criar backup")
        
    except Exception as e:
        print(f"[ERRO] Erro durante o backup: {e}")
    finally:
        await conn.close()
        print("[CLOSE] Conexão fechada")

if __name__ == "__main__":
    asyncio.run(main())
