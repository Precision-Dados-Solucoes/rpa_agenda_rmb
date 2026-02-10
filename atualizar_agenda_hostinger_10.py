#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualiza a tabela agenda_base no MySQL Hostinger a partir do arquivo
atualizar-agenda-10.xlsx na pasta raiz do projeto.

- Reutiliza o processamento de atualizar_agenda_downloads.py (colunas de data/hora
  tratadas: inicio, conclusao_prevista, conclusao_efetiva, prazo_fatal, cadastro).
- Faz UPSERT na agenda_base (chave: id_legalone).
- Atualiza apenas o MySQL Hostinger (não altera Supabase).

Uso (na raiz do projeto):
  python atualizar_agenda_hostinger_10.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv("config.env")

# Arquivo na raiz do projeto
RAIZ = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(RAIZ, "atualizar-agenda-10.xlsx")


def main():
    from atualizar_agenda_downloads import process_excel_file
    from hostinger_mysql_helper import upsert_agenda_base

    print("=" * 70)
    print("🔄 ATUALIZAÇÃO DA TABELA AGENDA_BASE (MySQL Hostinger)")
    print("   Arquivo: atualizar-agenda-10.xlsx (raiz do projeto)")
    print("=" * 70)

    if not os.path.isfile(ARQUIVO):
        print(f"\n❌ Arquivo não encontrado: {ARQUIVO}")
        sys.exit(1)

    print(f"\n📂 Processando: {ARQUIVO}")
    df = process_excel_file(ARQUIVO)
    if df is None or df.empty:
        print("\n❌ Nenhum dado processado. Verifique o arquivo e as colunas.")
        sys.exit(1)

    print(f"\n📊 Linhas a processar: {len(df)}")
    print("\n📤 Enviando para MySQL Hostinger (agenda_base)...")
    ok = upsert_agenda_base(df, "agenda_base", "id_legalone")

    if ok:
        print("\n✅ Tabela agenda_base atualizada no MySQL Hostinger com sucesso!")
    else:
        print("\n❌ Falha ao atualizar. Verifique config.env (MYSQL_*) e o arquivo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
