# Agendamento – Processos Novos e Processos Encerrados

## Horários

| RPA                  | Horário  | Ação                                                                 |
|----------------------|----------|----------------------------------------------------------------------|
| **Processos Novos**  | 19:00    | Relatório id=679 → tratativas → INSERT na tabela `processos_base` (Hostinger) |
| **Processos Encerrados** | 19:30 | Relatório id=680 → tratativas → UPDATE `data_sentenca`, `data_encerramento_resultado_tipo_resultado`, `status` por `id` (Hostinger) |

---

## GitHub Actions (já configurado)

Os workflows estão em `.github/workflows/`:

- **rpa_processos_novos_schedule.yml** – executa diariamente às 19:00 (BRT)
- **rpa_processos_encerrados_schedule.yml** – executa diariamente às 19:30 (BRT)

**Secrets necessários no repositório** (Settings → Secrets and variables → Actions):

- `NOVAJUS_USERNAME`
- `NOVAJUS_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT` (opcional; padrão 3306)
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

Também é possível disparar manualmente em Actions → escolher o workflow → Run workflow.

---

## Opção 1: Script agendador (local)

1. Instale a dependência: `pip install schedule`
2. Execute e deixe rodando (ex.: em uma janela de terminal ou como serviço):
   ```bash
   python agendador_processos.py
   ```
   - Às 19:00 executa `rpa_processos_novos.py`
   - Às 19:30 executa `rpa_processos_encerrados.py`

---

## Opção 2: Agendador de Tarefas do Windows

Crie **duas** tarefas:

### Tarefa 1 – Processos Novos (19:00)

- **Nome:** RPA Processos Novos
- **Gatilho:** Diariamente, às 19:00
- **Ação:** Iniciar um programa
  - **Programa:** `python` (ou caminho completo do `python.exe`)
  - **Argumentos:** `"C:\...\rpa_agenda_rmb\rpa_processos_novos.py"`
  - **Iniciar em:** `C:\...\rpa_agenda_rmb`

### Tarefa 2 – Processos Encerrados (19:30)

- **Nome:** RPA Processos Encerrados
- **Gatilho:** Diariamente, às 19:30
- **Ação:** Iniciar um programa
  - **Programa:** `python` (ou caminho completo do `python.exe`)
  - **Argumentos:** `"C:\...\rpa_agenda_rmb\rpa_processos_encerrados.py"`
  - **Iniciar em:** `C:\...\rpa_agenda_rmb`

Substitua `C:\...\rpa_agenda_rmb` pelo caminho real da pasta do projeto.

---

## Banco Hostinger – tabela `processos_base`

Para **Processos Encerrados**, a tabela precisa das colunas:

- `data_sentenca` (DATETIME, opcional)
- `data_encerramento_resultado_tipo_resultado` (DATETIME, opcional)
- `status` (VARCHAR, opcional)

Se ainda não existirem, execute no MySQL (phpMyAdmin ou cliente):

```sql
ALTER TABLE processos_base ADD COLUMN data_sentenca DATETIME NULL;
ALTER TABLE processos_base ADD COLUMN data_encerramento_resultado_tipo_resultado DATETIME NULL;
ALTER TABLE processos_base ADD COLUMN status VARCHAR(255) NULL;
```

Scripts de criação/alter da tabela estão em `scripts/create_tables_hostinger_mysql.sql`.
