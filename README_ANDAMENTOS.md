# RPA Andamentos - Automação de Relatórios

Este projeto automatiza a extração, processamento e inserção de dados de andamentos do sistema Legal One/Novajus para o Supabase.

## 📋 Funcionalidades

- **Download automático** de relatórios de andamentos
- **Processamento de dados** com tratamentos específicos
- **Sistema UPSERT** (atualiza se existe, insere se novo)
- **Agendamento automático** (12h e 17h, segunda a sexta)
- **Interface gráfica** para demonstração

## 🕐 Agendamento

O RPA é executado automaticamente:
- **Segunda a Sexta: 12:00 BRT**
- **Segunda a Sexta: 17:00 BRT**
- **Fuso horário:** São Paulo (BRT)

## 🗄️ Estrutura do Banco

### Tabela: `andamento_base`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_agenda_legalone` | int8 | ID da agenda no Legal One |
| `id_andamento` | int8 | ID do andamento (chave primária) |
| `tipo_andamento` | text | Tipo do andamento |
| `subtipo_andamento` | text | Subtipo do andamento |
| `descricao_andamento` | text | Descrição do andamento |
| `cadastro_andamento` | date | Data de cadastro (formato: aaaa/mm/dd) |

### Sistema UPSERT

- **Comparação:** `id_andamento_legalone` (arquivo) ↔ `id_andamento` (banco)
- **Se existe:** Atualiza o registro
- **Se não existe:** Insere novo registro

## 🚀 Configuração

### 1. Instalar dependências

```bash
python setup_andamentos_rpa.py
```

### 2. Configurar credenciais

Edite o arquivo `config.env`:

```env
# Credenciais Novajus
NOVAJUS_USERNAME=seu_email@exemplo.com
NOVAJUS_PASSWORD=sua_senha

# Credenciais Supabase
SUPABASE_HOST=db.exemplo.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua_senha_supabase
```

### 3. Executar manualmente

```bash
python rpa_andamentos_completo.py
```

## 📁 Arquivos do Projeto

### Scripts Principais
- `rpa_andamentos_completo.py` - RPA completo (download + processamento + UPSERT)
- `rpa_andamentos_clean.py` - Versão limpa para download
- `process_andamentos_to_supabase.py` - Processamento e UPSERT

### Configuração
- `setup_andamentos_rpa.py` - Configuração automática
- `requirements_andamentos.txt` - Dependências Python
- `config.env` - Credenciais (criado automaticamente)

### GitHub Actions
- `.github/workflows/rpa_andamentos_schedule.yml` - Agendamento automático

## 🔄 Fluxo de Execução

1. **Login** no sistema Novajus
2. **Seleção** da licença correta
3. **Navegação** para relatório de andamentos (ID 672)
4. **Geração** do relatório
5. **Download** do arquivo Excel
6. **Processamento** dos dados
7. **UPSERT** no Supabase (tabela `andamento_base`)

## 📊 Tratamento de Dados

### Mapeamento de Colunas

| Arquivo Excel | Supabase | Tratamento |
|---------------|----------|------------|
| `id_agenda_legalone` | `id_agenda_legalone` | int8 |
| `id_andamento_legalone` | `id_andamento` | int8 |
| `tipo_andamento` | `tipo_andamento` | text |
| `subtipo_andamento` | `subtipo_andamento` | text |
| `descricao_andamento` | `descricao_andamento` | text |
| `cadastro_andamento` | `cadastro_andamento` | date (dd/mm/aaaa hh:mm:ss → aaaa/mm/dd) |

### Conversões Automáticas

- **Datas:** `dd/mm/aaaa hh:mm:ss` → `aaaa/mm/dd`
- **Tipos:** Conversão automática para int8, text, date
- **Validação:** Verificação de integridade dos dados

## 🔧 Configuração do GitHub Actions

### Secrets Necessários

Configure os seguintes secrets no GitHub:

```
NOVAJUS_USERNAME=seu_email@exemplo.com
NOVAJUS_PASSWORD=sua_senha
SUPABASE_HOST=db.exemplo.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua_senha_supabase
```

### Execução Manual

Para executar manualmente no GitHub:

1. Vá para **Actions** no repositório
2. Selecione **RPA Andamentos - Agendamento Automático**
3. Clique em **Run workflow**
4. Configure o modo de teste se necessário

## 📈 Monitoramento

### Logs de Execução

- Screenshots automáticos em cada etapa
- Logs detalhados de processamento
- Relatórios de registros inseridos/atualizados

### Arquivos de Debug

- `debug_andamentos_*.png` - Screenshots de cada etapa
- `downloads/` - Arquivos baixados
- Logs do GitHub Actions

## 🛠️ Solução de Problemas

### Erro de Conexão
- Verifique as credenciais no `config.env`
- Teste a conexão com o Supabase
- Verifique se a tabela `andamento_base` existe

### Erro de Download
- Verifique as credenciais do Novajus
- Confirme se o relatório ID 672 está acessível
- Verifique se a licença está correta

### Erro de Processamento
- Verifique se o arquivo foi baixado corretamente
- Confirme se as colunas esperadas existem
- Verifique os logs de processamento

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs de execução
2. Confirme as configurações
3. Teste a execução manual primeiro

## 🔄 Atualizações

O sistema é atualizado automaticamente via GitHub Actions. Para atualizações manuais:

1. Faça pull das últimas alterações
2. Execute `python setup_andamentos_rpa.py`
3. Teste a execução manual
4. Faça push para ativar o agendamento automático
