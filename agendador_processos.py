#!/usr/bin/env python3
"""
Agendador dos RPAs Processos Novos e Processos Encerrados.
- Processos Novos: diariamente às 19:00 (relatório id=679 -> INSERT processos_base)
- Processos Encerrados: diariamente às 19:30 (relatório id=680 -> UPDATE processos_base)

Execute este script e deixe rodando (ex.: em segundo plano ou como serviço).
Alternativa: use o Agendador de Tarefas do Windows (ver AGENDAMENTO_PROCESSOS.md).
"""

import schedule
import time
import subprocess
import sys
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))


def run_processos_novos():
    print("\n[AGENDADOR] Executando RPA Processos Novos (19:00)...")
    try:
        subprocess.run(
            [sys.executable, os.path.join(RAIZ, "rpa_processos_novos.py")],
            cwd=RAIZ,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("[AGENDADOR] Processos Novos: timeout 10 min.")
    except Exception as e:
        print(f"[AGENDADOR] Erro ao executar Processos Novos: {e}")


def run_processos_encerrados():
    print("\n[AGENDADOR] Executando RPA Processos Encerrados (19:30)...")
    try:
        subprocess.run(
            [sys.executable, os.path.join(RAIZ, "rpa_processos_encerrados.py")],
            cwd=RAIZ,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("[AGENDADOR] Processos Encerrados: timeout 10 min.")
    except Exception as e:
        print(f"[AGENDADOR] Erro ao executar Processos Encerrados: {e}")


def main():
    schedule.every().day.at("19:00").do(run_processos_novos)
    schedule.every().day.at("19:30").do(run_processos_encerrados)
    print("Agendador ativo:")
    print("  - Processos Novos: diariamente às 19:00")
    print("  - Processos Encerrados: diariamente às 19:30")
    print("Pressione Ctrl+C para encerrar.\n")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
