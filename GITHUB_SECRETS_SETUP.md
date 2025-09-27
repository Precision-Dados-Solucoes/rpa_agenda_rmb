# 🔐 Configuração dos Secrets do GitHub Actions

## 📋 **Secrets Necessários**

Para o GitHub Actions funcionar, você precisa configurar os seguintes secrets no seu repositório:

### **1. Acesse as Configurações do Repositório**
- Vá para o seu repositório no GitHub
- Clique em **"Settings"** (Configurações)
- No menu lateral, clique em **"Secrets and variables"** → **"Actions"**

### **2. Adicione os Secrets**

#### **🔗 Secrets do Supabase:**
```
SUPABASE_HOST = db.dhfmqumwizrwdbjnbcua.supabase.co
SUPABASE_PORT = 5432
SUPABASE_DATABASE = postgres
SUPABASE_USER = postgres
SUPABASE_PASSWORD = **PDS2025@@
SUPABASE_TABLE_NAME = agenda_base
DATABASE_URL = postgresql://postgres:**PDS2025@@@db.dhfmqumwizrwdbjnbcua.supabase.co:5432/postgres?sslmode=require
```

> **📝 IMPORTANTE:** A `DATABASE_URL` é mais confiável que conexões individuais. 
> **Formato:** `postgresql://postgres:<SENHA>@db.<PROJECT>.supabase.co:5432/postgres?sslmode=require`
> **SSL obrigatório:** O `sslmode=require` é necessário para conexões seguras.

#### **🔐 Secrets do Novajus:**
```
NOVAJUS_USERNAME = cleiton.sanches@precisionsolucoes.com
NOVAJUS_PASSWORD = PDS2025@
```

### **3. Como Adicionar um Secret**

1. **Clique em "New repository secret"**
2. **Digite o nome** (ex: `SUPABASE_HOST`)
3. **Digite o valor** (ex: `db.dhfmqumwizrwdbjnbcua.supabase.co`)
4. **Clique em "Add secret"**

### **4. Verificação**

Após adicionar todos os secrets, você pode:
- **Executar manualmente** o workflow em **"Actions"** → **"RPA Agenda RMB"** → **"Run workflow"**
- **Verificar os logs** da execução

## ⏰ **Agendamento**

O RPA está configurado para executar:
- **📅 Diariamente às 07:00 (horário de São Paulo)**
- **🔄 Automaticamente via GitHub Actions**

## 🚀 **Execução Manual**

Para testar antes do agendamento:
1. Vá em **"Actions"** no GitHub
2. Clique em **"RPA Agenda RMB - Execução Diária"**
3. Clique em **"Run workflow"**
4. Aguarde a execução
5. Verifique os logs
