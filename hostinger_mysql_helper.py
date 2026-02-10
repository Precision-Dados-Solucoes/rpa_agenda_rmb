"""
Módulo auxiliar para UPSERT de agenda_base e andamento_base no MySQL da Hostinger.
Usado pelos RPAs após atualizar o Supabase.
Credenciais: config.env (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE).
Tratamento de colunas de data/hora: converte valores do DataFrame (date, time, datetime) para formato MySQL.
"""

import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv("config.env")

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "srv1890.hstgr.io"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "charset": "utf8mb4",
}


def get_hostinger_connection():
    """Conecta ao MySQL da Hostinger."""
    if not MYSQL_CONFIG.get("user") or not MYSQL_CONFIG.get("password"):
        print("[HOSTINGER] [ERRO] MYSQL_USER e MYSQL_PASSWORD devem estar no config.env")
        return None
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except Exception as e:
        print(f"[HOSTINGER] [ERRO] Erro ao conectar ao MySQL: {e}")
        return None


def _valor_para_mysql(val, col_name):
    """
    Converte valor do DataFrame para formato aceito pelo MySQL.
    Trata date -> YYYY-MM-DD, time -> HH:MM:SS, datetime -> YYYY-MM-DD HH:MM:SS.
    """
    if val is None or pd.isna(val):
        return None
    tname = type(val).__name__
    if tname in ("datetime", "Timestamp") or isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(val) else None
    if tname == "time":
        return val.strftime("%H:%M:%S")
    if tname == "date":
        return val.strftime("%Y-%m-%d")
    if hasattr(val, "isoformat"):
        s = val.isoformat()
        if "T" in s or (len(s) >= 19 and s[10] == " "):
            return s[:19].replace("T", " ")
        if len(s) >= 10:
            return s[:10]
        return s
    s = str(val).strip()
    if not s:
        return None
    # Já em formato MySQL
    if len(s) == 8 and s.count(":") == 2 and s.replace(":", "").isdigit():
        return s  # HH:MM:SS
    if len(s) >= 19 and s[10] == " " and s[4] == "-":
        return s[:19]  # YYYY-MM-DD HH:MM:SS
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s  # YYYY-MM-DD
    # Tentar parsear datas
    if "data" in col_name.lower() or "cadastro" in col_name.lower() or "hora" in col_name.lower() or "inicio" in col_name.lower() or "conclusao" in col_name.lower() or "prazo" in col_name.lower():
        try:
            dt = pd.to_datetime(s, errors="coerce")
            if pd.notna(dt):
                if "hora" in col_name.lower() and "data" not in col_name.lower():
                    return dt.strftime("%H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if float(val).is_integer():
            return int(val)
        return float(val)
    return s if s else None


def upsert_agenda_base(df, table_name="agenda_base", primary_key="id_legalone"):
    """
    Faz UPSERT na tabela agenda_base no MySQL Hostinger.
    UPDATE se existe (por id_legalone), INSERT se não existe.
    Converte colunas de data/hora do DataFrame para formato MySQL (DATE/TIME/DATETIME).
    """
    conn = None
    try:
        conn = get_hostinger_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            AND COLUMN_NAME != 'id' AND COLUMN_NAME != 'created_at'
            ORDER BY ORDINAL_POSITION
            """,
            (MYSQL_CONFIG["database"], table_name),
        )
        table_columns = [row[0] for row in cursor.fetchall()]

        columns_df = [c for c in df.columns.tolist() if c in table_columns]
        if primary_key not in columns_df:
            print(f"[HOSTINGER] [ERRO] Chave '{primary_key}' não encontrada no DataFrame")
            return False

        inserted = 0
        updated = 0
        skipped = 0

        cols_sql = ", ".join(f"`{c}`" for c in columns_df)
        placeholders = ", ".join(["%s"] * len(columns_df))
        insert_sql = f"INSERT INTO `{table_name}` ({cols_sql}) VALUES ({placeholders})"

        for _, row in df.iterrows():
            id_value = row.get(primary_key)
            if id_value is None or pd.isna(id_value):
                skipped += 1
                continue

            cursor.execute(
                f"SELECT `{primary_key}` FROM `{table_name}` WHERE `{primary_key}` = %s",
                (id_value,),
            )
            exists = cursor.fetchone()

            values = [_valor_para_mysql(row.get(c), c) for c in columns_df]

            if exists:
                set_parts = [f"`{c}` = %s" for c in columns_df if c != primary_key]
                update_values = [_valor_para_mysql(row.get(c), c) for c in columns_df if c != primary_key]
                update_values.append(id_value)
                cursor.execute(
                    f"UPDATE `{table_name}` SET {', '.join(set_parts)} WHERE `{primary_key}` = %s",
                    update_values,
                )
                updated += 1
            else:
                cursor.execute(insert_sql, values)
                inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[HOSTINGER] [OK] {table_name}: Inseridos={inserted}, Atualizados={updated}, Pulados={skipped}")
        return True

    except Exception as e:
        print(f"[HOSTINGER] [ERRO] UPSERT {table_name}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def upsert_andamento_base(df, table_name="andamento_base", primary_key="id_andamento_legalone"):
    """
    Faz UPSERT na tabela andamento_base no MySQL Hostinger.
    UPDATE se existe (por id_andamento_legalone), INSERT se não existe.
    Converte cadastro_andamento para DATETIME MySQL (YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD 00:00:00).
    """
    conn = None
    try:
        conn = get_hostinger_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            AND COLUMN_NAME != 'id' AND COLUMN_NAME != 'created_at'
            ORDER BY ORDINAL_POSITION
            """,
            (MYSQL_CONFIG["database"], table_name),
        )
        table_columns = [row[0] for row in cursor.fetchall()]

        columns_df = [c for c in df.columns.tolist() if c in table_columns]
        if primary_key not in columns_df:
            print(f"[HOSTINGER] [ERRO] Chave '{primary_key}' não encontrada no DataFrame")
            return False

        inserted = 0
        updated = 0
        skipped = 0

        cols_sql = ", ".join(f"`{c}`" for c in columns_df)
        placeholders = ", ".join(["%s"] * len(columns_df))
        insert_sql = f"INSERT INTO `{table_name}` ({cols_sql}) VALUES ({placeholders})"

        for _, row in df.iterrows():
            id_value = row.get(primary_key)
            if id_value is None or pd.isna(id_value):
                skipped += 1
                continue

            cursor.execute(
                f"SELECT `{primary_key}` FROM `{table_name}` WHERE `{primary_key}` = %s",
                (id_value,),
            )
            exists = cursor.fetchone()

            values = []
            for c in columns_df:
                val = row.get(c)
                # cadastro_andamento: garantir DATETIME (se for só date -> 00:00:00)
                if c == "cadastro_andamento" and val is not None and not pd.isna(val):
                    v = _valor_para_mysql(val, c)
                    if v and len(v) == 10:  # YYYY-MM-DD
                        v = v + " 00:00:00"
                    values.append(v)
                else:
                    values.append(_valor_para_mysql(val, c))

            if exists:
                set_parts = [f"`{c}` = %s" for c in columns_df if c != primary_key]
                update_values = []
                for c in columns_df:
                    if c == primary_key:
                        continue
                    val = row.get(c)
                    if c == "cadastro_andamento" and val is not None and not pd.isna(val):
                        v = _valor_para_mysql(val, c)
                        if v and len(v) == 10:
                            v = v + " 00:00:00"
                        update_values.append(v)
                    else:
                        update_values.append(_valor_para_mysql(val, c))
                update_values.append(id_value)
                cursor.execute(
                    f"UPDATE `{table_name}` SET {', '.join(set_parts)} WHERE `{primary_key}` = %s",
                    update_values,
                )
                updated += 1
            else:
                cursor.execute(insert_sql, values)
                inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[HOSTINGER] [OK] {table_name}: Inseridos={inserted}, Atualizados={updated}, Pulados={skipped}")
        return True

    except Exception as e:
        print(f"[HOSTINGER] [ERRO] UPSERT {table_name}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def update_agenda_ultimo_andamento(df_andamentos):
    """
    Atualiza na tabela agenda_base as colunas do último andamento por agenda.
    Chave: id_agenda_legalone (andamento) = id_legalone (agenda_base).
    Para cada id_agenda_legalone considera o último andamento (maior cadastro_andamento)
    e atualiza em agenda_base:
      cadastro_andamento -> data_ultimo_andamento (DATETIME)
      tipo_andamento      -> tipo_ultimo_andamento (TEXT)
      descricao_andamento -> conteudo_ultimo_andamento (TEXT)
    """
    required = ["id_agenda_legalone", "cadastro_andamento", "tipo_andamento", "descricao_andamento"]
    if not all(c in df_andamentos.columns for c in required):
        print("[HOSTINGER] [ERRO] update_agenda_ultimo_andamento: DataFrame precisa das colunas:", required)
        return False
    # Último andamento por id_agenda_legalone (maior cadastro_andamento)
    df = df_andamentos.sort_values("cadastro_andamento", ascending=False, na_position="last")
    df = df.drop_duplicates(subset=["id_agenda_legalone"], keep="first")
    conn = None
    try:
        conn = get_hostinger_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        updated = 0
        for _, row in df.iterrows():
            id_agenda = row.get("id_agenda_legalone")
            if id_agenda is None or pd.isna(id_agenda):
                continue
            # data_ultimo_andamento: DATETIME (cadastro_andamento pode ser date -> 00:00:00)
            v_cadastro = row.get("cadastro_andamento")
            if v_cadastro is not None and not pd.isna(v_cadastro):
                data_ultimo = _valor_para_mysql(v_cadastro, "cadastro_andamento")
                if data_ultimo and len(data_ultimo) == 10:
                    data_ultimo = data_ultimo + " 00:00:00"
            else:
                data_ultimo = None
            # tipo_ultimo_andamento: TEXT (relatório: tipo_andamento)
            v_tipo = row.get("tipo_andamento")
            tipo_ultimo = None if (v_tipo is None or pd.isna(v_tipo)) else str(v_tipo).strip() or None
            # conteudo_ultimo_andamento: TEXT
            v_desc = row.get("descricao_andamento")
            conteudo_ultimo = None if (v_desc is None or pd.isna(v_desc)) else str(v_desc).strip() or None
            cursor.execute(
                """
                UPDATE agenda_base
                SET data_ultimo_andamento = %s, tipo_ultimo_andamento = %s, conteudo_ultimo_andamento = %s
                WHERE id_legalone = %s
                """,
                (data_ultimo, tipo_ultimo, conteudo_ultimo, id_agenda),
            )
            updated += cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[HOSTINGER] [OK] agenda_base: {updated} registros atualizados (data/tipo/conteudo último andamento)")
        return True
    except Exception as e:
        print(f"[HOSTINGER] [ERRO] update_agenda_ultimo_andamento: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


# URL base para link de processos (usado em insert_processos_base)
LINK_PROCESSOS_BASE = "https://robertomatos.novajus.com.br/processos/processos/details/"
LINK_PROCESSOS_PARAMS = "?hasNavigation=True&currentPage=1&returnUrl=%2Fprocessos%2Fprocessos%2Fsearch%3Fajaxnavigation%3Dtrue"


def _parse_data_apenas(val):
    """Converte valor (Excel dd/mm/aaaa ou datetime) para MySQL datetime (só data): YYYY-MM-DD 00:00:00."""
    if val is None or pd.isna(val):
        return None
    tname = type(val).__name__
    if tname in ("datetime", "Timestamp") or isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d 00:00:00") if pd.notna(val) else None
    if tname == "date":
        return val.strftime("%Y-%m-%d 00:00:00")
    s = str(val).strip()
    if not s:
        return None
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            dt = pd.to_datetime(s, format=fmt, errors="raise")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d 00:00:00")
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d 00:00:00")
    except Exception:
        pass
    return None


def insert_processos_base(df, table_name="processos_base"):
    """
    Insere registros na tabela processos_base (processos novos).
    Espera DataFrame com coluna 'id' (obrigatório). Gera 'link' se não existir.
    Trata data_cadastro para formato MySQL datetime (só data).
    Usa INSERT ... ON DUPLICATE KEY UPDATE para não falhar em id duplicado.
    """
    conn = None
    try:
        conn = get_hostinger_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            AND COLUMN_NAME != 'created_at'
            ORDER BY ORDINAL_POSITION
            """,
            (MYSQL_CONFIG["database"], table_name),
        )
        table_columns = [row[0] for row in cursor.fetchall()]

        # Garantir id e link no df
        df = df.copy()
        if "id" not in df.columns:
            id_col = next((c for c in df.columns if str(c).strip().lower() == "id"), None)
            if id_col is not None:
                df["id"] = df[id_col]
            else:
                print("[HOSTINGER] [ERRO] Coluna 'id' não encontrada no DataFrame para processos_base")
                return False
        if "link" not in df.columns:
            df["link"] = df["id"].apply(
                lambda x: f"{LINK_PROCESSOS_BASE}{int(x)}{LINK_PROCESSOS_PARAMS}" if x is not None and not pd.isna(x) else None
            )
        if "data_cadastro" in table_columns and "data_cadastro" in df.columns:
            df["data_cadastro"] = df["data_cadastro"].apply(lambda v: _parse_data_apenas(v))

        columns_df = [c for c in df.columns.tolist() if c in table_columns]
        if "id" not in columns_df:
            columns_df.insert(0, "id")
        if "link" in table_columns and "link" not in columns_df:
            columns_df.append("link")

        inserted = 0
        cols_sql = ", ".join(f"`{c}`" for c in columns_df)
        placeholders = ", ".join(["%s"] * len(columns_df))
        update_parts = [f"`{c}` = VALUES(`{c}`)" for c in columns_df if c != "id"]
        sql = f"INSERT INTO `{table_name}` ({cols_sql}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE " + ", ".join(update_parts)

        for _, row in df.iterrows():
            id_val = row.get("id")
            if id_val is None or pd.isna(id_val):
                continue
            values = [_valor_para_mysql(row.get(c), c) for c in columns_df]
            cursor.execute(sql, values)
            inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[HOSTINGER] [OK] {table_name} (processos novos): {inserted} registros inseridos/atualizados")
        return True

    except Exception as e:
        print(f"[HOSTINGER] [ERRO] insert_processos_base: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def update_processos_encerrados(df, table_name="processos_base"):
    """
    Atualiza na tabela processos_base as colunas data_sentenca, data_encerramento_resultado_tipo_resultado e status.
    Chave: coluna id.
    """
    conn = None
    try:
        conn = get_hostinger_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        df = df.copy()

        # Normalizar nomes de colunas (Excel pode vir com variações)
        def find_col(df, *names):
            for n in names:
                if n in df.columns:
                    return n
                low = str(n).strip().lower().replace(" ", "_")
                for c in df.columns:
                    if str(c).strip().lower().replace(" ", "_") == low:
                        return c
            return None

        id_col = find_col(df, "id", "Id", "ID")
        if not id_col:
            print("[HOSTINGER] [ERRO] Coluna 'id' não encontrada no DataFrame para processos encerrados")
            return False

        col_data_sentenca = find_col(df, "data_sentenca", "data sentenca")
        col_data_encerramento = find_col(df, "data_encerramento_resultado_tipo_resultado", "data_encerramento", "data encerramento resultado tipo resultado")
        col_status = find_col(df, "status", "Status")

        updated = 0
        sql = """
            UPDATE `{table}` SET
                `data_sentenca` = %s,
                `data_encerramento_resultado_tipo_resultado` = %s,
                `status` = %s
            WHERE `id` = %s
        """.format(table=table_name).strip()

        for _, row in df.iterrows():
            id_val = row.get(id_col)
            if id_val is None or pd.isna(id_val):
                continue
            id_val = int(id_val)
            data_sentenca = _parse_data_apenas(row.get(col_data_sentenca)) if col_data_sentenca else None
            data_encerramento = _parse_data_apenas(row.get(col_data_encerramento)) if col_data_encerramento else None
            status = row.get(col_status) if col_status else None
            if status is not None and pd.isna(status):
                status = None
            else:
                status = str(status).strip() if status else None
            cursor.execute(sql, (data_sentenca, data_encerramento, status, id_val))
            if cursor.rowcount > 0:
                updated += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[HOSTINGER] [OK] {table_name} (processos encerrados): {updated} registros atualizados")
        return True

    except Exception as e:
        print(f"[HOSTINGER] [ERRO] update_processos_encerrados: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
