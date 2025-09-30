# 📊 Análise de Agenda Diária

## Descrição
Script automatizado que gera análise visual dos dados de agenda com status "Pendente" e sem andamento "1. Produzido", enviando gráficos por email.

## Funcionalidades
- ✅ Conexão com Supabase
- ✅ Análise de dados em tempo real
- ✅ Geração de 4 tipos de gráficos
- ✅ Envio automático por email
- ✅ Agendamento via GitHub Actions

## Gráficos Gerados
1. **👥 Distribuição por Executante** - Gráfico de barras
2. **🏷️ Distribuição por Etiqueta** - Gráfico de pizza
3. **📋 Distribuição por Tipo/Subtipo** - Gráfico horizontal
4. **📊 Dashboard Resumo** - Visão geral completa

## Configuração

### 1. Instalar Dependências
```bash
# Windows
install_analise_dependencies.bat

# Linux/Mac
pip install -r requirements_analise.txt
```

### 2. Configurar Variáveis de Ambiente
```env
# Supabase
SUPABASE_HOST=db.dhfmqumwizrwdbjnbcua.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua_senha

# Gmail
GMAIL_USERNAME=rmbautomacoes@gmail.com
GMAIL_PASSWORD=sua_senha_de_app
```

### 3. Executar Manualmente
```bash
python analise_agenda_dados.py
```

## Agendamento Automático

### GitHub Actions
- **Frequência:** Segunda a sexta-feira
- **Horário:** 08:30 BRT (11:30 UTC)
- **Destinatários:**
  - cleiton.sanches@precisionsolucoes.com
  - controladoria@gestaogt.onmicrosoft.com

### Execução Manual
O workflow pode ser executado manualmente no GitHub Actions.

## Estrutura do Email

### Conteúdo
- 📊 Resumo da análise com estatísticas
- 🖼️ Gráficos incorporados no corpo do email
- 📎 Anexos como backup (para clientes que bloqueiam imagens)
- 📝 Nota explicativa sobre os anexos

### Formato
- **Assunto:** "Análise de agenda diária - [data]"
- **Remetente:** rmbautomacoes@gmail.com
- **Layout:** Responsivo e profissional

## Troubleshooting

### Problemas Comuns
1. **Imagens não aparecem:** Verificar anexos do email
2. **Erro de conexão:** Verificar credenciais do Supabase
3. **Erro de email:** Verificar credenciais do Gmail

### Logs
O script gera logs detalhados durante a execução:
- ✅ Conexão com banco
- ✅ Análise de dados
- ✅ Geração de gráficos
- ✅ Envio de email

## Arquivos Gerados
- `grafico_executante.png`
- `grafico_etiqueta.png`
- `grafico_tipo_subtipo.png`
- `dashboard_analise_agenda.png`

## Manutenção
- Os arquivos PNG são gerados a cada execução
- Os gráficos são automaticamente anexados ao email
- Logs são exibidos no console durante a execução