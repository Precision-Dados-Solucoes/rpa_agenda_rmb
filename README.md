# RPA Agenda RMB

Este projeto automatiza a extração de dados do sistema Novajus e o armazenamento no Supabase através de um processo de RPA (Robotic Process Automation).

## 🚀 Funcionalidades

- Login automático no sistema Novajus
- Seleção automática de licença
- Geração e download de relatórios
- Processamento de dados Excel/CSV
- Inserção automática no banco de dados Supabase
- Execução agendada via GitHub Actions

## 📋 Pré-requisitos

- Python 3.10+
- Conta no Supabase
- Acesso ao sistema Novajus
- Git e GitHub

## 🛠️ Instalação

1. **Clone o repositório:**
```bash
git clone <seu-repositorio>
cd rpa_agenda_rmb
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Instale o Playwright:**
```bash
playwright install chromium
```

4. **Configure as variáveis de ambiente:**
```bash
cp env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Configurações do Supabase
SUPABASE_HOST=db.<seu_project_id>.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua_senha_do_banco
SUPABASE_TABLE_NAME=minha_tabela_de_relatorios

# Configurações do Novajus (opcional)
NOVAJUS_USERNAME=seu_email@exemplo.com
NOVAJUS_PASSWORD=sua_senha

# Configuração do modo headless
HEADLESS=false
```

## 🏃‍♂️ Execução

### Execução Local

```bash
python rpa_agenda_rmb.py
```

### Teste de Inserção no Supabase

Para testar apenas a inserção no Supabase (sem executar o RPA completo):

1. Coloque um arquivo Excel na pasta `downloads/`
2. Descomente a linha de teste no final do script:
```python
asyncio.run(test_supabase_insertion())
```
3. Execute o script

## 🔧 Configuração do GitHub Actions

1. **Configure os secrets no GitHub:**
   - Vá em Settings > Secrets and variables > Actions
   - Adicione os seguintes secrets:
     - `SUPABASE_HOST`
     - `SUPABASE_PORT`
     - `SUPABASE_DATABASE`
     - `SUPABASE_USER`
     - `SUPABASE_PASSWORD`

2. **O workflow será executado automaticamente:**
   - Todo dia às 09:00 UTC
   - Manualmente via "Actions" > "Run workflow"

## 📁 Estrutura do Projeto

```
rpa_agenda_rmb/
├── .github/
│   └── workflows/
│       └── rpa-daily.yml          # Workflow do GitHub Actions
├── downloads/                      # Pasta para arquivos baixados
├── rpa_agenda_rmb.py              # Script principal
├── requirements.txt                # Dependências Python
├── env.example                    # Exemplo de variáveis de ambiente
└── README.md                      # Este arquivo
```

## 🗄️ Estrutura da Tabela Supabase

O script espera uma tabela com as seguintes colunas:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| lo_pasta | text | Número da pasta |
| lo_numerocnj | text | Número CNJ |
| lo_numeroantigo | text | Número antigo |
| lo_outronumero | text | Outro número |
| lo_cliente | text | Cliente principal |
| lo_contrario | text | Contrário principal |
| lo_acao | text | Ação |
| data_publicacao | date | Data da publicação |
| lo_tipoandamento | text | Tipo de andamento |
| lo_descricao | text | Descrição |
| lo_idpubli | text | ID da publicação |
| origem_dados | text | Origem dos dados (fixo: 'LegalOne') |

## 🐛 Debug

O script gera capturas de tela de debug em caso de erro:
- `debug_initial_page.png`
- `debug_after_login.png`
- `debug_report_page.png`
- E outros...

## 📝 Logs

O script exibe logs detalhados durante a execução, incluindo:
- Status de cada etapa
- URLs visitadas
- Erros encontrados
- Progresso do download
- Status da inserção no banco

## ⚠️ Troubleshooting

### Erro de Timeout
- Verifique sua conexão com a internet
- Aumente os timeouts no código se necessário

### Erro de Login
- Verifique as credenciais no arquivo `.env`
- Confirme se o sistema Novajus está acessível

### Erro de Supabase
- Verifique as credenciais do Supabase
- Confirme se a tabela existe e tem a estrutura correta

### Erro de Download
- Verifique se a pasta `downloads/` existe
- Confirme se há espaço em disco suficiente

## 📞 Suporte

Para problemas ou dúvidas, verifique:
1. Os logs de execução
2. As capturas de tela de debug
3. A configuração das variáveis de ambiente
4. A estrutura da tabela no Supabase

## 🔄 Atualizações

Para atualizar o script:
1. Faça as alterações necessárias
2. Teste localmente
3. Faça commit e push para o GitHub
4. O GitHub Actions executará automaticamente na próxima execução agendada
