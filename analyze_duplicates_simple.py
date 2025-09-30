#!/usr/bin/env python3
"""
Script para análise detalhada de duplicados na tabela agenda_base
Versão simplificada sem emojis para compatibilidade com Windows
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import pandas as pd

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

async def analyze_duplicates_detailed(conn):
    """Análise detalhada de duplicados"""
    print("\n[ANALYSIS] ANALISE DETALHADA DE DUPLICADOS")
    print("="*50)
    
    # 1. Estatísticas gerais
    total_count = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
    print(f"[STATS] Total de registros: {total_count}")
    
    # 2. Contagem por status
    status_query = """
        SELECT status, COUNT(*) as count
        FROM agenda_base 
        GROUP BY status
        ORDER BY count DESC
    """
    status_counts = await conn.fetch(status_query)
    print(f"\n[STATUS] Registros por status:")
    for status, count in status_counts:
        print(f"  - {status or 'NULL'}: {count}")
    
    # 3. Identificar duplicados
    duplicates_query = """
        SELECT id_legalone, COUNT(*) as count
        FROM agenda_base 
        WHERE id_legalone IS NOT NULL
        GROUP BY id_legalone 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """
    
    duplicates = await conn.fetch(duplicates_query)
    print(f"\n[DUPLICATES] Registros duplicados por id_legalone: {len(duplicates)}")
    
    if not duplicates:
        print("[OK] Nenhum duplicado encontrado!")
        return
    
    # 4. Análise detalhada dos duplicados
    print(f"\n[TOP] TOP 20 DUPLICADOS:")
    for i, (id_legalone, count) in enumerate(duplicates[:20]):
        print(f"  {i+1:2d}. id_legalone: {id_legalone} - {count} ocorrencias")
    
    # 5. Análise por status dos duplicados
    print(f"\n[DETAILS] ANALISE POR STATUS DOS DUPLICADOS:")
    
    for id_legalone, count in duplicates[:10]:  # Analisar apenas os 10 primeiros
        print(f"\n[ITEM] id_legalone: {id_legalone} ({count} registros)")
        
        detail_query = """
            SELECT id, status, compromisso_tarefa, executante, 
                   cadastro, created_at
            FROM agenda_base 
            WHERE id_legalone = $1
            ORDER BY created_at DESC, id DESC
        """
        
        records = await conn.fetch(detail_query, id_legalone)
        
        # Agrupar por status
        status_groups = {}
        for record in records:
            status = record['status'] or 'NULL'
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(record)
        
        for status, group in status_groups.items():
            print(f"  [GROUP] Status '{status}': {len(group)} registros")
            for record in group:
                created = record['created_at'].strftime('%Y-%m-%d %H:%M:%S') if record['created_at'] else 'NULL'
                print(f"    - ID: {record['id']}, Created: {created}")
    
    # 6. Resumo das regras de limpeza
    print(f"\n[RULES] RESUMO DAS REGRAS DE LIMPEZA:")
    print("  1. Se houver diferentes status:")
    print("     - Manter: 'Cumprido com parecer' > 'Cumprido' > 'Pendente'")
    print("     - Deletar: registros de menor prioridade")
    print("  2. Se mesmo status:")
    print("     - Manter: apenas o mais recente (created_at)")
    print("     - Deletar: os demais")
    
    # 7. Simulação de limpeza
    print(f"\n[SIMULATION] SIMULACAO DE LIMPEZA:")
    total_to_delete = 0
    
    for id_legalone, count in duplicates:
        detail_query = """
            SELECT id, status, created_at
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
        
        total_to_delete += len(to_delete)
        
        if len(duplicates) <= 5:  # Mostrar detalhes apenas para os primeiros 5
            print(f"  [ITEM] id_legalone: {id_legalone}")
            print(f"    [KEEP] Manter: ID {to_keep['id']} (Status: {to_keep['status']})")
            for record in to_delete:
                print(f"    [DELETE] Deletar: ID {record['id']} (Status: {record['status']})")
    
    print(f"\n[SUMMARY] RESUMO DA SIMULACAO:")
    print(f"  - Total de duplicados: {len(duplicates)}")
    print(f"  - Registros a serem deletados: {total_to_delete}")
    print(f"  - Registros a serem mantidos: {len(duplicates)}")

async def main():
    """Função principal"""
    print("ANALISE DE DUPLICADOS - TABELA AGENDA_BASE")
    print("="*50)
    print("[INFO] Este script apenas ANALISA - não faz alterações no banco")
    
    # Conectar ao banco
    conn = await connect_to_supabase()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco")
        return
    
    try:
        await analyze_duplicates_detailed(conn)
        
    except Exception as e:
        print(f"[ERRO] Erro durante a análise: {e}")
    finally:
        await conn.close()
        print("\n[CLOSE] Conexão fechada")

if __name__ == "__main__":
    asyncio.run(main())
