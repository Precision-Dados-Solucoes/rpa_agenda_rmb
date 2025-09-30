#!/usr/bin/env python3
"""
Workflow simplificado para limpeza da tabela agenda_base
Versão sem emojis para compatibilidade com Windows
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Executa um script Python"""
    print(f"\n{'='*60}")
    print(f"[STEP] {description}")
    print(f"[FILE] Script: {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("[OK] Script executado com sucesso!")
            if result.stdout:
                print("[OUTPUT] Saida:")
                print(result.stdout)
        else:
            print("[ERRO] Erro na execucao do script!")
            if result.stderr:
                print("[ERROR] Erro:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[ERRO] Erro ao executar {script_name}: {e}")
        return False
    
    return True

def main():
    """Workflow principal"""
    print("WORKFLOW DE LIMPEZA DA TABELA AGENDA_BASE")
    print("="*60)
    print("[INFO] Este workflow ira:")
    print("  1. [BACKUP] Fazer backup da tabela")
    print("  2. [ANALYSIS] Analisar duplicados")
    print("  3. [CLEANUP] Limpar duplicados (com confirmacao)")
    print("  4. [VERIFY] Verificar resultado")
    print()
    
    # Verificar se os scripts existem
    scripts = [
        "backup_agenda_simple.py",
        "analyze_duplicates_simple.py", 
        "cleanup_duplicates_simple.py"
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"[ERRO] Script nao encontrado: {script}")
            return
    
    print("[OK] Todos os scripts encontrados!")
    
    # Etapa 1: Backup
    print("\n" + "="*60)
    print("ETAPA 1: BACKUP")
    print("="*60)
    
    if not run_script("backup_agenda_simple.py", "Criando backup da tabela"):
        print("[ERRO] Falha no backup. Abortando workflow.")
        return
    
    # Etapa 2: Análise
    print("\n" + "="*60)
    print("ETAPA 2: ANALISE")
    print("="*60)
    
    if not run_script("analyze_duplicates_simple.py", "Analisando duplicados"):
        print("[ERRO] Falha na analise. Abortando workflow.")
        return
    
    # Etapa 3: Confirmação
    print("\n" + "="*60)
    print("ETAPA 3: CONFIRMACAO")
    print("="*60)
    
    print("[WARNING] ATENCAO: A proxima etapa ira DELETAR registros duplicados!")
    print("[RULES] Regras de limpeza:")
    print("  - Manter registros com status 'Cumprido' ou 'Cumprido com parecer'")
    print("  - Deletar registros com status 'Pendente'")
    print("  - Se mesmo status, manter apenas o mais recente")
    print()
    print("[BACKUP] Backup foi criado na etapa anterior")
    
    confirm = input("[CONFIRM] Deseja continuar com a limpeza? (s/N): ").lower().strip()
    
    if confirm != 's':
        print("[CANCEL] Limpeza cancelada pelo usuario")
        print("[BACKUP] Backup esta disponivel para uso futuro")
        return
    
    # Etapa 4: Limpeza
    print("\n" + "="*60)
    print("ETAPA 4: LIMPEZA")
    print("="*60)
    
    if not run_script("cleanup_duplicates_simple.py", "Limpando duplicados"):
        print("[ERRO] Falha na limpeza.")
        return
    
    # Etapa 5: Verificação final
    print("\n" + "="*60)
    print("ETAPA 5: VERIFICACAO FINAL")
    print("="*60)
    
    print("[VERIFY] Executando analise final para verificar resultado...")
    run_script("analyze_duplicates_simple.py", "Verificando resultado da limpeza")
    
    print("\n" + "="*60)
    print("[SUCCESS] WORKFLOW CONCLUIDO!")
    print("="*60)
    print("[SUMMARY] Resumo:")
    print("  [OK] Backup criado")
    print("  [OK] Duplicados analisados")
    print("  [OK] Limpeza executada")
    print("  [OK] Resultado verificado")
    print()
    print("[BACKUP] Backup disponivel para restauracao se necessario")

if __name__ == "__main__":
    main()
