# ✅ Correção: Workflow RPA Agenda Não Configurava Azure SQL

## 🔍 Problema Identificado

O workflow `rpa_agenda_schedule.yml` **não estava configurando as variáveis de ambiente do Azure SQL**, então quando o script `rpa_agenda_rmb.py` tentava fazer o upsert no Azure SQL, ele falhava silenciosamente porque as variáveis não existiam.

### Comparação

**Workflow `rpa_agenda_schedule.yml` (ANTES - ERRADO):**
```yaml
- name: Configurar variáveis de ambiente
  run: |
    echo "NOVAJUS_USERNAME=${{ secrets.NOVAJUS_USERNAME }}" >> $GITHUB_ENV
    echo "NOVAJUS_PASSWORD=${{ secrets.NOVAJUS_PASSWORD }}" >> $GITHUB_ENV
    echo "SUPABASE_HOST=${{ secrets.SUPABASE_HOST }}" >> $GITHUB_ENV
    # ... apenas Supabase, SEM Azure SQL!
```

**Workflow `rpa_atualiza_agenda_677_schedule.yml` (CORRETO):**
```yaml
- name: Configurar variáveis de ambiente
  run: |
    # ... Supabase ...
    echo "AZURE_SERVER=${{ secrets.AZURE_SERVER }}" >> $GITHUB_ENV
    echo "AZURE_DATABASE=${{ secrets.AZURE_DATABASE }}" >> $GITHUB_ENV
    echo "AZURE_USER=${{ secrets.AZURE_USER }}" >> $GITHUB_ENV
    echo "AZURE_PASSWORD=${{ secrets.AZURE_PASSWORD }}" >> $GITHUB_ENV
    echo "AZURE_PORT=${{ secrets.AZURE_PORT }}" >> $GITHUB_ENV
```

## ✅ Correção Aplicada

Adicionei as variáveis do Azure SQL ao workflow `rpa_agenda_schedule.yml`:

```yaml
- name: Configurar variáveis de ambiente
  run: |
    echo "NOVAJUS_USERNAME=${{ secrets.NOVAJUS_USERNAME }}" >> $GITHUB_ENV
    echo "NOVAJUS_PASSWORD=${{ secrets.NOVAJUS_PASSWORD }}" >> $GITHUB_ENV
    echo "SUPABASE_HOST=${{ secrets.SUPABASE_HOST }}" >> $GITHUB_ENV
    echo "SUPABASE_PORT=${{ secrets.SUPABASE_PORT }}" >> $GITHUB_ENV
    echo "SUPABASE_DATABASE=${{ secrets.SUPABASE_DATABASE }}" >> $GITHUB_ENV
    echo "SUPABASE_USER=${{ secrets.SUPABASE_USER }}" >> $GITHUB_ENV
    echo "SUPABASE_PASSWORD=${{ secrets.SUPABASE_PASSWORD }}" >> $GITHUB_ENV
    # ✅ ADICIONADO: Variáveis do Azure SQL
    echo "AZURE_SERVER=${{ secrets.AZURE_SERVER }}" >> $GITHUB_ENV
    echo "AZURE_DATABASE=${{ secrets.AZURE_DATABASE }}" >> $GITHUB_ENV
    echo "AZURE_USER=${{ secrets.AZURE_USER }}" >> $GITHUB_ENV
    echo "AZURE_PASSWORD=${{ secrets.AZURE_PASSWORD }}" >> $GITHUB_ENV
    echo "AZURE_PORT=${{ secrets.AZURE_PORT }}" >> $GITHUB_ENV
```

## 🔍 Verificar Outros Workflows

Preciso verificar se outros workflows também estão faltando as variáveis do Azure SQL:

- [ ] `rpa_atualiza_concluidos_schedule.yml`
- [ ] `rpa_atualiza_cumpridos_parecer_schedule.yml`
- [ ] `rpa_andamentos_schedule.yml`
- [ ] Outros workflows que atualizam o Azure SQL

## 📋 Próximos Passos

1. ✅ **Correção aplicada** no `rpa_agenda_schedule.yml`
2. ⏳ **Verificar outros workflows** e corrigir se necessário
3. ⏳ **Verificar se os secrets estão configurados** no GitHub:
   - `AZURE_SERVER`
   - `AZURE_DATABASE`
   - `AZURE_USER`
   - `AZURE_PASSWORD`
   - `AZURE_PORT`
4. ⏳ **Testar** executando o workflow manualmente

## 🚨 Importante

Certifique-se de que os **secrets do Azure SQL estão configurados** no GitHub:

1. Acesse: Settings → Secrets and variables → Actions
2. Verifique se existem:
   - `AZURE_SERVER`
   - `AZURE_DATABASE`
   - `AZURE_USER`
   - `AZURE_PASSWORD`
   - `AZURE_PORT`

Se não existirem, adicione-os com os valores corretos do seu `config.env`.

---

**Data da Correção:** 19/01/2026
