# Lista de RPAs executados pelo GitHub Actions

Horários em **horário de Brasília (BRT, UTC-3)**.  
Arquivos de workflow em `.github/workflows/` (apenas os ativos, sem " - Copia").

---

| Workflow | Horário de execução | Ação / Script executado |
|----------|---------------------|-------------------------|
| **RPA Agenda 682** (`rpa_agenda_682_schedule.yml`) | **A cada hora** (00:00 a 23:00 BRT) | Baixa relatório id=682, UPSERT em agenda_base (apenas MySQL Hostinger). **Script:** `python rpa_agenda_682_rmb.py` |
| **RPA Agenda** (`rpa_agenda_schedule.yml`) | 11:10, 14:10 e 16:10 (todos os dias) | Baixa relatório de agenda (id=671), processa e atualiza Supabase + MySQL Hostinger. **Script:** `python rpa_agenda_rmb.py` |
| **RPA Andamentos** (`rpa_andamentos_schedule.yml`) | 12:10 e 17:10 (segunda a sexta) | Baixa relatório de andamentos, processa e atualiza Supabase + MySQL Hostinger; atualiza último andamento em agenda_base. **Script:** `python rpa_andamentos_completo.py` |
| **RPA Atualização de Agenda 677** (`rpa_atualiza_agenda_677_schedule.yml`) | 12:10, 16:10 e 18:10 (todos os dias) | Baixa relatório 677, atualiza agenda_base. **Script:** `python rpa_atualiza_agenda_677_rmb.py` |
| **RPA Atualização de Concluídos** (`rpa_atualiza_concluidos_schedule.yml`) | 12:15, 14:15, 15:15 e 16:45 (segunda a sexta) | Baixa relatório de concluídos (id=673), atualiza agenda_base. **Script:** `python rpa_atualiza_concluidos_rmb.py` |
| **RPA Atualização de Cumpridos com Parecer** (`rpa_atualiza_cumpridos_parecer_schedule.yml`) | 13:10 e 16:15 (segunda a sexta) | Baixa relatório de cumpridos com parecer, atualiza agenda_base. **Script:** `python rpa_atualiza_cumpridos_com_parecer_rmb.py` |
| **RPA Relatório Diário** (`rpa_daily_report.yml`) | 08:30 e 17:15 (segunda a sexta) | Envia e-mail com relatório diário de agendamentos. **Script:** `python send_daily_agenda_report.py` |
| **RPA Prazos Fatais do Dia** (`rpa_prazos_fatais_dia.yml`) | 08:00 (todos os dias) | Envia e-mail com prazos fatais do dia. **Script:** `python rpa_prazos_fatais_dia.py` |
| **RPA Processos Novos** (`rpa_processos_novos_schedule.yml`) | 19:10 (todos os dias) | Processos novos, atualiza MySQL Hostinger. **Script:** `python rpa_processos_novos.py` |
| **RPA Processos Encerrados** (`rpa_processos_encerrados_schedule.yml`) | 19:30 (todos os dias) | Processos encerrados, atualiza base. **Script:** `python rpa_processos_encerrados.py` |
| **RPA Relatório de Agenda sem Interação** (`rpa_agenda_no_interaction_report.yml`) | 17:15 (segunda a sexta) | Envia relatório de agenda sem interação por e-mail. **Script:** `python send_agenda_no_interaction_report.py` |
| **Análise de Agenda Diária** (`analise_agenda_diaria.yml`) | 08:30 (segunda a sexta) | Executa análise de agenda e gera gráficos. **Script:** `python analise_agenda_dados.py` |

---

## Resumo por horário (BRT)

| Horário | Workflows |
|---------|-----------|
| **A cada hora** | RPA Agenda 682 (00:00 a 23:00 BRT) |
| **08:00** | RPA Prazos Fatais do Dia |
| **08:30** | RPA Relatório Diário, Análise de Agenda Diária |
| **11:10** | RPA Agenda |
| **12:10** | RPA Atualização Agenda 677, RPA Andamentos (seg–sex) |
| **12:15** | RPA Atualização de Concluídos (seg–sex) |
| **13:10** | RPA Atualização de Cumpridos com Parecer (seg–sex) |
| **14:10** | RPA Agenda |
| **14:15** | RPA Atualização de Concluídos (seg–sex) |
| **15:15** | RPA Atualização de Concluídos (seg–sex) |
| **16:10** | RPA Agenda, RPA Atualização Agenda 677 |
| **16:15** | RPA Atualização de Cumpridos com Parecer (seg–sex) |
| **16:45** | RPA Atualização de Concluídos (seg–sex) |
| **17:10** | RPA Andamentos (seg–sex) |
| **17:15** | RPA Relatório Diário, RPA Relatório Agenda sem Interação (seg–sex) |
| **18:10** | RPA Atualização Agenda 677 |
| **19:10** | RPA Processos Novos |
| **19:30** | RPA Processos Encerrados |

---

## Observações

- **RPA Agenda 682** roda a cada hora (cron `0 * * * *` em UTC). Os demais workflows que antes rodavam no minuto :00 foram deslocados em 10 minutos para não conflitar (ex.: RPA Agenda 11:00 → 11:10 BRT).
- **Resumo de execução:** os RPAs que fazem UPSERT em agenda_base (Agenda 671, Agenda 682, Atualização 677, Concluídos, Cumpridos com Parecer) exibem no log a linha `RESUMO: N itens processados (inseridos: X, atualizados: Y, pulados: Z)`.
- **RPA Publicações:** o arquivo `rpa_publicacoes_schedule.yml` está vazio no repositório; se esse workflow for usado, é preciso definir o cron e o script no arquivo.
- Todos os workflows podem ser disparados manualmente via **workflow_dispatch** (quando configurado).
- Os horários no repositório estão em **UTC** (cron do GitHub); na tabela acima foram convertidos para **BRT**.
