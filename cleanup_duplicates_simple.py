#!/usr/bin/env python3
"""
Script para limpar duplicados na tabela agenda_base
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

async def analyze_duplicates(conn):
    """Analisa duplicados na tabela"""
    print("\n[ANALYSIS] ANALISANDO DUPLICADOS...")
    
    # 1. Contar total de registros
    total_count = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
    print(f"[STATS] Total de registros na tabela: {total_count}")
    
    # 2. Identificar duplicados por id_legalone
    duplicates_query = """
        SELECT id_legalone, COUNT(*) as count
        FROM agenda_base 
        WHERE id_legalone IS NOT NULL
        GROUP BY id_legalone 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """
    
    duplicates = await conn.fetch(duplicates_query)
    print(f"[DUPLICATES] Registros duplicados por id_legalone: {len(duplicates)}")
    
    if duplicates:
        print("\n[TOP] TOP 10 DUPLICADOS:")
        for i, (id_legalone, count) in enumerate(duplicates[:10]):
            print(f"  {i+1}. id_legalone: {id_legalone} - {count} ocorrencias")
    
    return duplicates

async def get_duplicate_details(conn, id_legalone):
    """Obtém detalhes dos registros duplicados para um id_legalone específico"""
    query = """
        SELECT id, id_legalone, status, compromisso_tarefa, executante, cadastro, 
               created_at
        FROM agenda_base 
        WHERE id_legalone = $1
        ORDER BY created_at DESC, id DESC
    """
    
    records = await conn.fetch(query, id_legalone)
    return records

async def cleanup_duplicates(conn):
    """Limpa duplicados seguindo as regras definidas"""
    print("\n[CLEANUP] INICIANDO LIMPEZA DE DUPLICADOS...")
    
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
    
    total_deleted = 0
    
    for id_legalone, count in duplicates:
        print(f"\n[PROCESS] Processando id_legalone: {id_legalone} ({count} registros)")
        
        # Obter detalhes dos registros
        records = await get_duplicate_details(conn, id_legalone)
        
        # Aplicar regras de limpeza
        records_to_keep = []
        records_to_delete = []
        
        # Regra 1: Priorizar status "Cumprido" e "Cumprido com parecer"
        status_priority = {
            "Cumprido com parecer": 1,
            "Cumprido": 2,
            "Pendente": 3
        }
        
        # Agrupar por status
        status_groups = {}
        for record in records:
            status = record['status'] or 'Pendente'
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(record)
        
        # Aplicar regras
        if len(status_groups) > 1:
            # Há diferentes status - manter os de maior prioridade
            best_status = min(status_groups.keys(), 
                            key=lambda x: status_priority.get(x, 999))
            records_to_keep = status_groups[best_status]
            
            # Deletar os de menor prioridade
            for status, group in status_groups.items():
                if status != best_status:
                    records_to_delete.extend(group)
        else:
            # Mesmo status - manter apenas o mais recente
            status = list(status_groups.keys())[0]
            group = status_groups[status]
            
            # Ordenar por created_at DESC e pegar o primeiro
            group.sort(key=lambda x: x['created_at'] or x['id'], reverse=True)
            records_to_keep = [group[0]]
            records_to_delete = group[1:]
        
        # Executar deleções
        if records_to_delete:
            delete_ids = [record['id'] for record in records_to_delete]
            delete_query = f"DELETE FROM agenda_base WHERE id = ANY($1)"
            result = await conn.execute(delete_query, delete_ids)
            
            deleted_count = int(result.split()[-1])
            total_deleted += deleted_count
            
            print(f"  [OK] Deletados {deleted_count} registros duplicados")
            print(f"  [KEEP] Mantidos: {len(records_to_keep)} registros")
            
            # Mostrar detalhes dos mantidos
            for record in records_to_keep:
                print(f"    - ID: {record['id']}, Status: {record['status']}, Created: {record['created_at']}")
        else:
            print(f"  [SKIP] Nenhum registro para deletar")
    
    return total_deleted

async def verify_cleanup(conn):
    """Verifica se a limpeza foi bem-sucedida"""
    print("\n[VERIFY] VERIFICANDO RESULTADO DA LIMPEZA...")
    
    # Contar registros restantes
    total_count = await conn.fetchval("SELECT COUNT(*) FROM agenda_base")
    print(f"[STATS] Total de registros após limpeza: {total_count}")
    
    # Verificar se ainda há duplicados
    duplicates_query = """
        SELECT id_legalone, COUNT(*) as count
        FROM agenda_base 
        WHERE id_legalone IS NOT NULL
        GROUP BY id_legalone 
        HAVING COUNT(*) > 1
    """
    
    remaining_duplicates = await conn.fetch(duplicates_query)
    print(f"[DUPLICATES] Duplicados restantes: {len(remaining_duplicates)}")
    
    if remaining_duplicates:
        print("[WARNING] Ainda existem duplicados:")
        for id_legalone, count in remaining_duplicates[:5]:
            print(f"  - id_legalone: {id_legalone} - {count} ocorrencias")
    else:
        print("[SUCCESS] Nenhum duplicado encontrado!")

async def main():
    """Função principal"""
    print("SCRIPT DE LIMPEZA DE DUPLICADOS - TABELA AGENDA_BASE")
    print("="*60)
    
    # Conectar ao banco
    conn = await connect_to_supabase()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco")
        return
    
    try:
        # Analisar duplicados
        duplicates = await analyze_duplicates(conn)
        
        if not duplicates:
            print("[OK] Nenhum duplicado encontrado!")
            return
        
        # Confirmar limpeza
        print(f"\n[WARNING] ATENCAO: {len(duplicates)} grupos de duplicados serão processados")
        print("[RULES] Regras de limpeza:")
        print("  1. Manter registros com status 'Cumprido' ou 'Cumprido com parecer'")
        print("  2. Deletar registros com status 'Pendente'")
        print("  3. Se mesmo status, manter apenas o mais recente")
        
        confirm = input("\n[CONFIRM] Deseja continuar com a limpeza? (s/N): ").lower().strip()
        
        if confirm != 's':
            print("[CANCEL] Limpeza cancelada pelo usuário")
            return
        
        # Executar limpeza
        deleted_count = await cleanup_duplicates(conn)
        
        # Verificar resultado
        await verify_cleanup(conn)
        
        print(f"\n[SUCCESS] LIMPEZA CONCLUIDA!")
        print(f"[STATS] Total de registros deletados: {deleted_count}")
        
    except Exception as e:
        print(f"[ERRO] Erro durante a limpeza: {e}")
    finally:
        await conn.close()
        print("[CLOSE] Conexão fechada")

if __name__ == "__main__":
    asyncio.run(main())
