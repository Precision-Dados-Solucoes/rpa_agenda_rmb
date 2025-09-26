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
```

#### **🔐 Secrets do Novajus:**
```
NOVAJUS_USERNAME = cleiton.sanches@precisionsolucoes.com
NOVAJUS_PASSWORD = PDS2025@
```

#### **📧 Secrets do Email:**
```
EMAIL_SERVER = smtp.office365.com
EMAIL_PORT = 587
EMAIL_USERNAME = seu_email@empresa.com
EMAIL_PASSWORD = sua_senha_do_office
EMAIL_FROM = seu_email@empresa.com
EMAIL_TO = destinatario@exemplo.com
```

### **3. Configuração de Email**

#### **📧 Para Microsoft Office 365/Outlook:**
```
EMAIL_SERVER = smtp.office365.com
EMAIL_PORT = 587
EMAIL_USERNAME = cleiton.sanches@precisionsolucoes.com
EMAIL_PASSWORD = sua_senha_normal_do_office
EMAIL_FROM = cleiton.sanches@precisionsolucoes.com
EMAIL_TO = cleiton.sanches@precisionsolucoes.com
```

#### **📧 Para Gmail (alternativa):**
```
EMAIL_SERVER = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USERNAME = seu_email@gmail.com
EMAIL_PASSWORD = senha_de_app_do_gmail
EMAIL_FROM = seu_email@gmail.com
EMAIL_TO = destinatario@exemplo.com
```

#### **📧 Para Outlook.com (Hotmail):**
```
EMAIL_SERVER = smtp-mail.outlook.com
EMAIL_PORT = 587
EMAIL_USERNAME = seu_email@outlook.com
EMAIL_PASSWORD = sua_senha_normal
EMAIL_FROM = seu_email@outlook.com
EMAIL_TO = destinatario@exemplo.com
```

### **4. Configuração do Microsoft Office 365**

#### **Para usar Office 365:**
1. **Use sua senha normal** da conta Microsoft
2. **Não precisa de senha de app** (diferente do Gmail)
3. **Configure os secrets** conforme mostrado acima

#### **Exemplo de configuração Office 365:**
```
EMAIL_SERVER = smtp.office365.com
EMAIL_PORT = 587
EMAIL_USERNAME = cleiton.sanches@precisionsolucoes.com
EMAIL_PASSWORD = PDS2025@  # Sua senha normal do Office
EMAIL_FROM = cleiton.sanches@precisionsolucoes.com
EMAIL_TO = cleiton.sanches@precisionsolucoes.com
```

### **4. Como Adicionar um Secret**

1. **Clique em "New repository secret"**
2. **Digite o nome** (ex: `SUPABASE_HOST`)
3. **Digite o valor** (ex: `db.dhfmqumwizrwdbjnbcua.supabase.co`)
4. **Clique em "Add secret"**

### **5. Verificação**

Após adicionar todos os secrets, você pode:
- **Executar manualmente** o workflow em **"Actions"** → **"RPA Agenda RMB"** → **"Run workflow"**
- **Verificar os logs** da execução
- **Receber emails** de sucesso/falha

## ⏰ **Agendamento**

O RPA está configurado para executar:
- **📅 Diariamente às 07:00 (horário de São Paulo)**
- **🔄 Automaticamente via GitHub Actions**
- **📧 Com envio de email de resultado**

## 🚀 **Execução Manual**

Para testar antes do agendamento:
1. Vá em **"Actions"** no GitHub
2. Clique em **"RPA Agenda RMB - Execução Diária"**
3. Clique em **"Run workflow"**
4. Aguarde a execução
5. Verifique os logs e emails
