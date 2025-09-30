#!/usr/bin/env python3
"""
Script para gerar lista de IDs que devem ser deletados manualmente
"""

import asyncio
import asyncpg
import os
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

async def generate_delete_list(conn):
    """Gera lista de IDs para deletar"""
    print("\n[ANALYSIS] GERANDO LISTA DE IDs PARA DELETAR...")
    
    # Obter lista de duplicados
    duplicates_query = """
        SELECT id_legalone, COUNT(*) as count
        FROM agenda_base 
        WHERE id_legalone IS NOT NULL
        GROUP BY id_legalone 
        HAVING COUNT(*) > 1
    """
    
    duplicates = await conn.fetch(duplicates_query)
    print(f"[FOUND] Encontrados {len(duplicates)} grupos de duplicados")
    
    ids_to_delete = []
    ids_to_keep = []
    
    for id_legalone, count in duplicates:
        print(f"\n[PROCESS] Processando id_legalone: {id_legalone} ({count} registros)")
        
        # Obter detalhes dos registros
        detail_query = """
            SELECT id, id_legalone, status, compromisso_tarefa, executante, 
                   cadastro, created_at
            FROM agenda_base 
            WHERE id_legalone = $1
            ORDER BY 
                CASE 
                    WHEN status = 'Cumprido com parecer' THEN 1
                    WHEN status = 'Cumprido' THEN 2
                    WHEN status = 'Pendente' THEN 3
                    ELSE 4
                END,
                created_at DESC, id DESC
        """
        
        records = await conn.fetch(detail_query, id_legalone)
        
        # Manter apenas o primeiro (maior prioridade)
        to_keep = records[0]
        to_delete = records[1:]
        
        ids_to_keep.append(to_keep['id'])
        for record in to_delete:
            ids_to_delete.append(record['id'])
        
        print(f"  [KEEP] Manter: ID {to_keep['id']} (Status: {to_keep['status']}, Created: {to_keep['created_at']})")
        for record in to_delete:
            print(f"  [DELETE] Deletar: ID {record['id']} (Status: {record['status']}, Created: {record['created_at']})")
    
    return ids_to_delete, ids_to_keep

async def save_delete_list(ids_to_delete, ids_to_keep):
    """Salva as listas em arquivos"""
    print(f"\n[SAVE] Salvando listas...")
    
    # Salvar IDs para deletar
    with open("ids_to_delete.txt", "w") as f:
        f.write("# Lista de IDs para deletar manualmente\n")
        f.write(f"# Total: {len(ids_to_delete)} registros\n")
        f.write("# Gerado em: " + str(pd.Timestamp.now()) + "\n\n")
        
        for i, id_val in enumerate(ids_to_delete, 1):
            f.write(f"{id_val}\n")
    
    # Salvar IDs para manter
    with open("ids_to_keep.txt", "w") as f:
        f.write("# Lista de IDs que serão mantidos\n")
        f.write(f"# Total: {len(ids_to_keep)} registros\n")
        f.write("# Gerado em: " + str(pd.Timestamp.now()) + "\n\n")
        
        for i, id_val in enumerate(ids_to_keep, 1):
            f.write(f"{id_val}\n")
    
    # Salvar SQL para deletar
    with open("delete_duplicates.sql", "w") as f:
        f.write("-- Script SQL para deletar duplicados\n")
        f.write(f"-- Total de registros: {len(ids_to_delete)}\n")
        f.write(f"-- Gerado em: " + str(pd.Timestamp.now()) + "\n\n")
        
        f.write("-- ATENÇÃO: Execute com cuidado!\n")
        f.write("-- Faça backup antes de executar!\n\n")
        
        # Gerar SQL em lotes de 100
        batch_size = 100
        for i in range(0, len(ids_to_delete), batch_size):
            batch = ids_to_delete[i:i+batch_size]
            ids_str = ",".join(map(str, batch))
            f.write(f"DELETE FROM agenda_base WHERE id IN ({ids_str});\n")
    
    print(f"[FILES] Arquivos criados:")
    print(f"  - ids_to_delete.txt ({len(ids_to_delete)} IDs)")
    print(f"  - ids_to_keep.txt ({len(ids_to_keep)} IDs)")
    print(f"  - delete_duplicates.sql (script SQL)")

async def main():
    """Função principal"""
    print("GERADOR DE LISTA DE IDs PARA DELETAR")
    print("="*50)
    
    # Conectar ao banco
    conn = await connect_to_supabase()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco")
        return
    
    try:
        # Gerar listas
        ids_to_delete, ids_to_keep = await generate_delete_list(conn)
        
        # Salvar arquivos
        await save_delete_list(ids_to_delete, ids_to_keep)
        
        print(f"\n[SUMMARY] RESUMO:")
        print(f"  - IDs para deletar: {len(ids_to_delete)}")
        print(f"  - IDs para manter: {len(ids_to_keep)}")
        print(f"  - Total de duplicados: {len(ids_to_delete) + len(ids_to_keep)}")
        
        print(f"\n[FILES] Arquivos gerados:")
        print(f"  - ids_to_delete.txt: Lista simples de IDs para deletar")
        print(f"  - ids_to_keep.txt: Lista de IDs que serão mantidos")
        print(f"  - delete_duplicates.sql: Script SQL pronto para executar")
        
        print(f"\n[INSTRUCTIONS] Para deletar manualmente:")
        print(f"  1. Use o arquivo 'delete_duplicates.sql' no Supabase")
        print(f"  2. Ou use a lista 'ids_to_delete.txt' para deletar um por um")
        print(f"  3. Verifique com 'ids_to_keep.txt' quais serão mantidos")
        
    except Exception as e:
        print(f"[ERRO] Erro durante a geração: {e}")
    finally:
        await conn.close()
        print("[CLOSE] Conexão fechada")

if __name__ == "__main__":
    import pandas as pd
    asyncio.run(main())
