#!/usr/bin/env python3
"""
Gera script SQL de UPSERT para a tabela agenda_base (MySQL) a partir de um Excel.
Carrega: atualiza-agenda-1703.xlsx da pasta Downloads do usuário.
Preserva as mesmas tratativas de campos dos RPAs (datas, link, etc.).
Não filtra por executante_sim (arquivo contém apenas executante Sim).

Uso:
  python gerar_sql_upsert_agenda_base.py

Saída: atualiza_agenda_base_upsert.sql (na pasta do projeto)
"""

import os
import pandas as pd
from pathlib import Path

# Caminho do Excel na pasta Downloads (Windows)
DOWNLOADS = Path(os.path.expanduser("~/Downloads"))
ARQUIVO_EXCEL = DOWNLOADS / "atualiza-agenda-1703.xlsx"
ARQUIVO_SQL_SAIDA = Path(__file__).resolve().parent / "atualiza_agenda_base_upsert.sql"

# Colunas da agenda_base que serão geradas no SQL (ordem do CREATE TABLE, sem id e created_at)
COLUNAS_AGENDA_BASE = [
    "id_legalone",
    "compromisso_tarefa",
    "tipo",
    "subtipo",
    "etiqueta",
    "inicio_data",
    "inicio_hora",
    "conclusao_prevista_data",
    "conclusao_prevista_hora",
    "conclusao_efetiva_data",
    "prazo_fatal_data",
    "pasta_proc",
    "numero_cnj",
    "executante",
    "executante_sim",
    "descricao",
    "status",
    "link",
    "cadastro",
    "cliente-processo",
    "contrario-processo",
]


def extract_date_from_datetime(datetime_val):
    """Extrai a data de dd/mm/aaaa hh:mm:ss ou dd/mm/aaaa hh:mm. Igual ao RPA."""
    if pd.isna(datetime_val) or datetime_val == "":
        return None
    try:
        if hasattr(datetime_val, "date"):
            return datetime_val.date() if pd.notna(datetime_val) else None
        s = str(datetime_val).strip()
        if not s:
            return None
        dt = pd.to_datetime(s, format="%d/%m/%Y %H:%M:%S", errors="coerce")
        if pd.isna(dt):
            dt = pd.to_datetime(s, format="%d/%m/%Y %H:%M", errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date()
    except Exception:
        return None


def extract_time_from_datetime(datetime_val):
    """Extrai a hora de dd/mm/aaaa hh:mm:ss. Igual ao RPA."""
    if pd.isna(datetime_val) or datetime_val == "":
        return None
    try:
        if hasattr(datetime_val, "time"):
            return datetime_val.time() if pd.notna(datetime_val) else None
        s = str(datetime_val).strip()
        if not s:
            return None
        dt = pd.to_datetime(s, format="%d/%m/%Y %H:%M:%S", errors="coerce")
        if pd.isna(dt):
            return None
        return dt.time()
    except Exception:
        return None


def generate_link(id_legalone):
    """Gera o link concatenado. Igual ao RPA."""
    if pd.isna(id_legalone):
        return None
    base_url = "https://robertomatos.novajus.com.br/agenda/compromissos/DetailsCompromissoTarefa/"
    params = "?hasNavigation=True&currentPage=1&returnUrl=%2Fagenda%2FCompromissoTarefa%2FSearch"
    return f"{base_url}{int(id_legalone)}{params}"


def _encontrar_coluna(df, opcoes):
    """Retorna o nome da coluna no df que está em opcoes (ex: Pasta_proc ou pasta_proc)."""
    for nome in opcoes:
        if nome in df.columns:
            return nome
    return None


def processar_excel(file_path):
    """
    Processa o Excel com as mesmas regras do RPA (rpa_atualiza_agenda_677_rmb).
    Não aplica filtro executante_sim.
    """
    print(f"Lendo: {file_path}")
    df = pd.read_excel(file_path)
    # Normalizar nomes de colunas (espaços, maiúsculas)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"Colunas no Excel: {df.columns.tolist()}")
    print(f"Linhas: {len(df)}")

    out = pd.DataFrame()

    # Mapeamento: coluna no banco -> coluna no Excel (pode ter variação de nome)
    mapeamento_direto = {
        "id_legalone": ["id_legalone"],
        "compromisso_tarefa": ["compromisso_tarefa"],
        "tipo": ["tipo"],
        "subtipo": ["subtipo"],
        "etiqueta": ["etiqueta"],
        "pasta_proc": ["Pasta_proc", "pasta_proc"],
        "numero_cnj": ["numero_cnj"],
        "executante": ["executante"],
        "executante_sim": ["executante_sim"],
        "descricao": ["descricao"],
        "status": ["status"],
        "cliente-processo": ["cliente-processo"],
        "contrario-processo": ["contrario-processo"],
    }

    for db_col, opcoes in mapeamento_direto.items():
        col_excel = _encontrar_coluna(df, opcoes)
        if col_excel is not None:
            out[db_col] = df[col_excel]
        else:
            out[db_col] = None

    # Campos de data/hora (tratamento igual ao RPA)
    if "inicio" in df.columns:
        out["inicio_data"] = df["inicio"].apply(extract_date_from_datetime)
        out["inicio_hora"] = df["inicio"].apply(extract_time_from_datetime)
    else:
        out["inicio_data"] = None
        out["inicio_hora"] = None

    if "conclusao_prevista" in df.columns:
        out["conclusao_prevista_data"] = df["conclusao_prevista"].apply(extract_date_from_datetime)
        out["conclusao_prevista_hora"] = df["conclusao_prevista"].apply(extract_time_from_datetime)
    else:
        out["conclusao_prevista_data"] = None
        out["conclusao_prevista_hora"] = None

    if "conclusao_efetiva" in df.columns:
        out["conclusao_efetiva_data"] = df["conclusao_efetiva"].apply(extract_date_from_datetime)
    else:
        out["conclusao_efetiva_data"] = None

    if "cadastro" in df.columns:
        out["cadastro"] = df["cadastro"].apply(extract_date_from_datetime)
    else:
        out["cadastro"] = None

    if "prazo_fatal" in df.columns:
        out["prazo_fatal_data"] = df["prazo_fatal"].apply(extract_date_from_datetime)
    else:
        out["prazo_fatal_data"] = None

    # Link
    if "id_legalone" in out.columns:
        out["link"] = out["id_legalone"].apply(generate_link)
    else:
        out["link"] = None

    # id_legalone numérico
    if "id_legalone" in out.columns:
        out["id_legalone"] = pd.to_numeric(out["id_legalone"], errors="coerce").astype("Int64")

    # Converter datas/horas para tipos nativos (evitar NaT em string)
    for col in ["inicio_data", "conclusao_prevista_data", "conclusao_efetiva_data", "prazo_fatal_data", "cadastro"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.date

    for col in ["inicio_hora", "conclusao_prevista_hora"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.time

    # Textos como string
    for col in ["pasta_proc", "numero_cnj", "executante", "executante_sim", "descricao", "link", "status",
                "compromisso_tarefa", "tipo", "subtipo", "etiqueta", "cliente-processo", "contrario-processo"]:
        if col in out.columns:
            out[col] = out[col].astype(str).replace("nan", "").replace("<NA>", "")

    # Remover linhas sem id_legalone válido
    out = out[out["id_legalone"].notna()].copy()
    print(f"Linhas após remover sem id_legalone: {len(out)}")
    return out


def valor_para_sql(val, col_name):
    """Converte valor do DataFrame para literal SQL (MySQL)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "NULL"
    if pd.isna(val) or (isinstance(val, str) and val in ("nan", "<NA>", "")):
        return "NULL"
    if hasattr(val, "isoformat"):
        if hasattr(val, "hour"):  # time
            return "'" + val.strftime("%H:%M:%S").replace("\\", "\\\\").replace("'", "''") + "'"
        return "'" + val.strftime("%Y-%m-%d").replace("\\", "\\\\").replace("'", "''") + "'"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and pd.isna(val):
            return "NULL"
        if float(val).is_integer():
            return str(int(val))
        return str(val)
    s = str(val).strip()
    if not s or s in ("nan", "NaN", "None", "<NA>"):
        return "NULL"
    return "'" + s.replace("\\", "\\\\").replace("'", "''") + "'"


def gerar_sql_upsert(df, colunas, arquivo_saida):
    """Gera arquivo .sql com INSERT ... ON DUPLICATE KEY UPDATE."""
    colunas_presentes = [c for c in colunas if c in df.columns]
    if "id_legalone" not in colunas_presentes:
        raise ValueError("id_legalone é obrigatório no DataFrame")

    linhas = []
    linhas.append("-- UPSERT agenda_base a partir de atualiza-agenda-1703.xlsx")
    linhas.append("-- Gerado por gerar_sql_upsert_agenda_base.py")
    linhas.append("-- Para UPSERT por id_legalone, é necessário ter chave única. Se ainda não tiver, execute antes:")
    linhas.append("-- ALTER TABLE agenda_base ADD UNIQUE KEY unique_id_legalone (id_legalone);")
    linhas.append("")
    linhas.append("USE u438744025_advromas;  -- Ajuste o nome do banco se necessário")
    linhas.append("")
    cols_sql = ", ".join(f"`{c}`" for c in colunas_presentes)
    update_parts = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in colunas_presentes if c != "id_legalone")

    valores_por_linha = []
    for _, row in df.iterrows():
        vals = [valor_para_sql(row.get(c), c) for c in colunas_presentes]
        valores_por_linha.append("(" + ", ".join(vals) + ")")

    # MySQL: INSERT ... VALUES (...), (...) ON DUPLICATE KEY UPDATE ... por lote
    lote = 100
    blocos = []
    for i in range(0, len(valores_por_linha), lote):
        chunk = valores_por_linha[i : i + lote]
        bloco = [
            f"INSERT INTO agenda_base ({cols_sql})",
            "VALUES",
            "  " + ",\n  ".join(chunk),
            f"ON DUPLICATE KEY UPDATE {update_parts};",
        ]
        blocos.append("\n".join(bloco))
    linhas.append("\n\n".join(blocos))

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"SQL gerado: {arquivo_saida} ({len(df)} linhas)")


def main():
    if not ARQUIVO_EXCEL.exists():
        print(f"Arquivo não encontrado: {ARQUIVO_EXCEL}")
        print("Coloque atualiza-agenda-1703.xlsx na pasta Downloads e execute novamente.")
        return 1
    df = processar_excel(ARQUIVO_EXCEL)
    if df.empty:
        print("Nenhum registro válido para gerar SQL.")
        return 1
    gerar_sql_upsert(df, COLUNAS_AGENDA_BASE, ARQUIVO_SQL_SAIDA)
    return 0


if __name__ == "__main__":
    exit(main())
