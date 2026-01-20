# 📋 Como Fazer UPSERT de Agenda e Andamentos no Azure SQL

## 🎯 Objetivo

Atualizar o banco Azure SQL com os relatórios mais recentes de agenda e andamentos.

## 📁 Preparação

1. **Extraia os relatórios** do Legal One/Novajus
2. **Salve os arquivos Excel** na pasta `downloads/` do projeto
   - Arquivo de agenda: qualquer nome com "agenda" (ex: `agenda_atualizada.xlsx`)
   - Arquivo de andamentos: qualquer nome com "andamento" (ex: `andamentos_atualizados.xlsx`)

## 🚀 Opção 1: Modo Automático (Recomendado)

O script procura automaticamente os arquivos mais recentes na pasta `downloads/`:

```cmd
python upsert_agenda_andamentos_azure_automatico.py
```

**Vantagens:**
- ✅ Automático - não precisa digitar caminhos
- ✅ Usa o arquivo mais recente automaticamente
- ✅ Mais rápido

## 🚀 Opção 2: Modo Interativo

Você informa os caminhos dos arquivos manualmente:

```cmd
python upsert_agenda_andamentos_azure.py
```

O script vai perguntar:
1. Caminho do arquivo de AGENDA (ou Enter para pular)
2. Caminho do arquivo de ANDAMENTOS (ou Enter para pular)

**Vantagens:**
- ✅ Você escolhe qual arquivo processar
- ✅ Pode processar apenas agenda ou apenas andamentos

## 📋 Requisitos dos Arquivos Excel

### Arquivo de Agenda
Deve conter a coluna:
- `id_legalone` (obrigatório)

### Arquivo de Andamentos
Deve conter a coluna:
- `id_andamento_legalone` (obrigatório)

## ✅ Verificação

Após o processamento, o script mostra:
- ✅ Quantos registros foram processados
- ✅ Se o upsert foi bem-sucedido
- ✅ Resumo final

## 🔍 Verificar Resultado

Para verificar se os dados foram atualizados:

```cmd
python verificar_status_azure_sql.py
```

Ou:

```cmd
python testar_conexao_azure_completo.py
```

## ⚠️ Importante

- Os arquivos devem estar em formato Excel (.xlsx ou .xls)
- O script faz **UPSERT** (UPDATE se existe, INSERT se não existe)
- Baseado na chave primária (`id_legalone` para agenda, `id_andamento_legalone` para andamentos)
- Não apaga dados existentes, apenas atualiza ou adiciona novos

## 🐛 Solução de Problemas

### Erro: "Arquivo não encontrado"
- Verifique se o arquivo está na pasta `downloads/`
- Use caminho absoluto se necessário

### Erro: "Coluna não encontrada"
- Verifique se o arquivo tem a coluna `id_legalone` (agenda) ou `id_andamento_legalone` (andamentos)
- Verifique se os nomes das colunas estão corretos

### Erro: "Não foi possível conectar ao Azure SQL"
- Verifique se o banco está online
- Verifique as credenciais no `config.env`
- Execute: `python testar_conexao_azure_completo.py`

---

**Após o upsert bem-sucedido, você pode fazer commit das alterações!**
