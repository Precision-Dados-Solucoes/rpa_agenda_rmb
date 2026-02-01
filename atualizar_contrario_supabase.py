#!/usr/bin/env python3
"""
Atualiza a coluna "contrario-processo" na tabela agenda_base do Supabase
a partir do arquivo atualiza-contrario.xlsx na pasta Downloads.

- Lê o Excel: coluna id_legalone (chave) + coluna com valor do contrário
- Atualiza em agenda_base apenas a coluna "contrario-processo" onde id_legalone coincide
- Coluna no banco está vazia: apenas preenchimento (UPDATE).
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Credenciais do Supabase (config.env na raiz do projeto)
load_dotenv("config.env")

# Caminho do arquivo: pasta PROJETOS RPA (pai da pasta rpa_agenda_rmb)
_PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETOS_RPA = os.path.dirname(_PASTA_SCRIPT)
ARQUIVO_EXCEL = os.path.join(PASTA_PROJETOS_RPA, "atualiza-contrario.xlsx")

COLUNA_CHAVE = "id_legalone"
COLUNA_ATUALIZAR = "contrario-processo"

# Possíveis nomes da coluna do valor no Excel (primeiro que existir será usado)
NOMES_COLUNA_CONTRARIO = [
    "contrario-processo",
    "contrario_processo",
    "contrario",
    "Contrário",
    "contrario processo",
]


def obter_conexao_supabase():
    """Conecta ao Supabase (PostgreSQL) usando variáveis de ambiente."""
    user = os.getenv("user") or os.getenv("SUPABASE_USER")
    password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
    host = os.getenv("host") or os.getenv("SUPABASE_HOST")
    port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
    dbname = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE")

    if not all([user, password, host, dbname]):
        raise ValueError(
            "Variáveis do Supabase incompletas. Configure SUPABASE_USER, SUPABASE_PASSWORD, "
            "SUPABASE_HOST, SUPABASE_DATABASE (ou user, password, host, dbname) no config.env"
        )

    return psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        dbname=dbname,
        sslmode="require",
    )


def carregar_excel(caminho):
    """Carrega o Excel e retorna DataFrame com id_legalone e o valor de contrario-processo."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_excel(caminho)
    df.columns = [str(c).strip() for c in df.columns]

    if COLUNA_CHAVE not in df.columns:
        raise ValueError(
            f"Coluna '{COLUNA_CHAVE}' não encontrada no arquivo. Colunas: {list(df.columns)}"
        )

    coluna_valor = None
    for nome in NOMES_COLUNA_CONTRARIO:
        if nome in df.columns:
            coluna_valor = nome
            break

    if coluna_valor is None:
        # Usar a segunda coluna se existir apenas id_legalone e mais uma
        outras = [c for c in df.columns if c != COLUNA_CHAVE]
        if len(outras) == 1:
            coluna_valor = outras[0]
        else:
            raise ValueError(
                f"Nenhuma coluna de valor encontrada. Esperada uma de: {NOMES_COLUNA_CONTRARIO}. "
                f"Colunas no arquivo: {list(df.columns)}"
            )

    # DataFrame com duas colunas: id_legalone e valor para "contrario-processo"
    resultado = df[[COLUNA_CHAVE, coluna_valor]].copy()
    resultado.columns = [COLUNA_CHAVE, COLUNA_ATUALIZAR]
    resultado[COLUNA_CHAVE] = pd.to_numeric(resultado[COLUNA_CHAVE], errors="coerce")
    resultado = resultado.dropna(subset=[COLUNA_CHAVE])
    resultado[COLUNA_CHAVE] = resultado[COLUNA_CHAVE].astype(int)

    return resultado


def atualizar_contrario_supabase(df):
    """Atualiza a coluna contrario-processo na agenda_base do Supabase por id_legalone."""
    conn = obter_conexao_supabase()
    cursor = conn.cursor()

    # Verificar se a coluna existe (PostgreSQL: colunas com hífen ficam em minúsculo entre aspas)
    cursor.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agenda_base' AND column_name = %s
    """, (COLUNA_ATUALIZAR,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(
            f"A coluna '{COLUNA_ATUALIZAR}' não existe na tabela agenda_base. "
            "Crie-a com: ALTER TABLE agenda_base ADD COLUMN \"contrario-processo\" TEXT;"
        )

    # Em PostgreSQL, identificadores com hífen precisam de aspas duplas
    update_sql = f'UPDATE agenda_base SET "{COLUNA_ATUALIZAR}" = %s WHERE id_legalone = %s'

    atualizados = 0
    nao_encontrados = 0

    for _, row in df.iterrows():
        id_legalone = row[COLUNA_CHAVE]
        valor = row[COLUNA_ATUALIZAR]
        if pd.isna(valor):
            valor = None
        else:
            valor = str(valor).strip() or None

        cursor.execute(update_sql, (valor, id_legalone))
        if cursor.rowcount > 0:
            atualizados += 1
        else:
            nao_encontrados += 1

    conn.commit()
    cursor.close()
    conn.close()

    return atualizados, nao_encontrados


def main(caminho_excel=None):
    caminho = caminho_excel or ARQUIVO_EXCEL
    print("=" * 60)
    print("Atualizar contrario-processo no Supabase (agenda_base)")
    print("=" * 60)
    print(f"Arquivo: {caminho}")
    print()

    df = carregar_excel(caminho)
    print(f"Linhas no Excel (com id_legalone válido): {len(df)}")
    print(f"Amostra:\n{df.head()}")
    print()

    print("Conectando ao Supabase...")
    atualizados, nao_encontrados = atualizar_contrario_supabase(df)

    print()
    print("Resultado:")
    print(f"  Atualizados (id_legalone encontrado na agenda_base): {atualizados}")
    print(f"  Sem correspondência (id_legalone não existe na agenda_base): {nao_encontrados}")
    print("Concluído.")


if __name__ == "__main__":
    import sys
    caminho = None
    if len(sys.argv) > 1:
        caminho = os.path.abspath(sys.argv[1])
    main(caminho)
