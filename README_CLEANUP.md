# 🧹 Scripts de Limpeza da Tabela Agenda Base

Este conjunto de scripts foi criado para limpar duplicados na tabela `agenda_base` seguindo regras específicas de negócio.

## 📋 Regras de Limpeza

### 1. Prioridade por Status
Quando há registros duplicados com diferentes status:
- **1ª Prioridade**: `Cumprido com parecer`
- **2ª Prioridade**: `Cumprido` 
- **3ª Prioridade**: `Pendente`

### 2. Mesmo Status
Quando há registros duplicados com o mesmo status:
- **Manter**: O registro mais recente (baseado em `created_at`)
- **Deletar**: Os demais registros

## 🛠️ Scripts Disponíveis

### 1. `backup_agenda_before_cleanup.py`
**Função**: Criar backup da tabela antes da limpeza
```bash
python backup_agenda_before_cleanup.py
```
- Cria arquivo Excel com todos os dados
- Inclui timestamp no nome do arquivo
- Mostra estatísticas do backup

### 2. `analyze_duplicates_agenda.py`
**Função**: Analisar duplicados (apenas leitura)
```bash
python analyze_duplicates_agenda.py
```
- Identifica registros duplicados
- Mostra estatísticas detalhadas
- Simula o que seria deletado
- **NÃO faz alterações no banco**

### 3. `cleanup_duplicates_agenda.py`
**Função**: Executar limpeza real
```bash
python cleanup_duplicates_agenda.py
```
- Aplica as regras de limpeza
- Solicita confirmação antes de deletar
- Mostra progresso da limpeza
- Verifica resultado final

### 4. `cleanup_agenda_workflow.py`
**Função**: Workflow completo automatizado
```bash
python cleanup_agenda_workflow.py
```
- Executa todos os scripts em sequência
- Backup → Análise → Confirmação → Limpeza → Verificação
- Interface amigável com confirmações

## 🚀 Como Usar

### Opção 1: Workflow Automatizado (Recomendado)
```bash
python cleanup_agenda_workflow.py
```
Este é o método mais seguro e completo.

### Opção 2: Execução Manual
```bash
# 1. Fazer backup
python backup_agenda_before_cleanup.py

# 2. Analisar duplicados
python analyze_duplicates_agenda.py

# 3. Executar limpeza (com confirmação)
python cleanup_duplicates_agenda.py
```

## ⚠️ Importante

### Antes de Executar
1. **Backup**: Sempre faça backup antes da limpeza
2. **Teste**: Execute primeiro `analyze_duplicates_agenda.py` para entender o que será deletado
3. **Confirmação**: O script de limpeza pede confirmação antes de deletar

### Segurança
- ✅ Todos os scripts fazem backup automático
- ✅ Confirmação obrigatória antes de deletar
- ✅ Logs detalhados de todas as operações
- ✅ Verificação do resultado após limpeza

## 📊 Exemplo de Saída

```
🔍 ANÁLISE DE DUPLICADOS - TABELA AGENDA_BASE
==================================================
📊 Total de registros: 1,250
🔍 Registros duplicados por id_legalone: 45

📋 TOP 20 DUPLICADOS:
  1. id_legalone: 12345 - 3 ocorrências
  2. id_legalone: 67890 - 2 ocorrências
  ...

🧮 SIMULAÇÃO DE LIMPEZA:
📊 RESUMO DA SIMULAÇÃO:
  - Total de duplicados: 45
  - Registros a serem deletados: 67
  - Registros a serem mantidos: 45
```

## 🔧 Configuração

Os scripts usam as mesmas credenciais do Supabase configuradas no arquivo `config.env`:

```env
SUPABASE_HOST=db.dhfmqumwizrwdbjnbcua.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=**PDS2025@@
```

## 🆘 Em Caso de Problemas

### Restaurar Backup
Se algo der errado, você pode restaurar o backup:
1. O backup é salvo como arquivo Excel
2. Use o Supabase Dashboard para importar os dados
3. Ou crie um script de restauração

### Verificar Resultado
Execute `analyze_duplicates_agenda.py` para verificar se ainda há duplicados.

## 📞 Suporte

Em caso de dúvidas ou problemas:
1. Verifique os logs de execução
2. Execute `analyze_duplicates_agenda.py` para diagnóstico
3. Use o backup para restaurar se necessário
