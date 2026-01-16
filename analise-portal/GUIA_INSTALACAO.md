# 🚀 Guia de Instalação - Portal de Análise

## 📋 Pré-requisitos

- Node.js 18 ou superior
- npm ou yarn
- Azure SQL Database configurado

## 🔧 Passo a Passo

### 1. Instalar Dependências

```bash
cd analise-portal
npm install
```

### 2. Configurar Variáveis de Ambiente

Crie o arquivo `.env.local` na raiz do projeto:

```env
# Azure SQL Database
# Formato: sqlserver://servidor:porta;database=nome_banco;user=usuario;password=senha;encrypt=true;trustServerCertificate=false
DATABASE_URL="sqlserver://bi-advromas.database.windows.net:1433;database=dbAdvromas;user=rpaautomacoes;password=SUA_SENHA_AQUI;encrypt=true;trustServerCertificate=false"

# JWT Secret (gere uma string aleatória segura)
JWT_SECRET="sua-chave-secreta-jwt-mude-isso-em-producao"

# Next.js
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="sua-chave-secreta-nextauth-mude-isso"
```

**Importante**: Substitua `SUA_SENHA_AQUI` pela senha real do Azure SQL Database.

### 3. Configurar Prisma

```bash
# Gerar cliente Prisma
npx prisma generate

# Puxar schema do banco existente (as tabelas já foram criadas)
npx prisma db pull
```

### 4. Executar em Desenvolvimento

```bash
npm run dev
```

O sistema estará disponível em: `http://localhost:3000`

## 🔐 Primeiro Acesso

1. Acesse: `http://localhost:3000/login`
2. Use as credenciais do usuário administrador criado:
   - Email: `cleiton.sanches@precisionsolucoes.com`
   - Senha: `Admin@2026` (ou a senha que você definiu)
3. Se for primeiro acesso, será redirecionado para trocar a senha
4. Após trocar a senha, será redirecionado para o dashboard

## 📁 Estrutura Criada

```
analise-portal/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx          ✅ Criado
│   │   └── trocar-senha/page.tsx   ✅ Criado
│   ├── (dashboard)/
│   │   └── dashboard/page.tsx      ✅ Criado
│   └── api/auth/
│       ├── login/route.ts          ✅ Criado
│       └── trocar-senha/route.ts   ✅ Criado
├── components/ui/                  ✅ Componentes shadcn
├── lib/
│   ├── prisma.ts                   ✅ Criado
│   └── auth.ts                     ✅ Criado
└── prisma/schema.prisma            ✅ Criado
```

## ✅ Funcionalidades Implementadas

- ✅ Página de login (email e senha)
- ✅ Verificação de primeiro acesso
- ✅ Página de troca de senha
- ✅ API de autenticação
- ✅ Geração de token JWT
- ✅ Criação de sessões
- ✅ Logs de acesso
- ✅ Dashboard básico (protegido)

## 🐛 Troubleshooting

### Erro: "Module not found: bcryptjs"
```bash
npm install bcryptjs @types/bcryptjs
```

### Erro: "Cannot connect to database"
- Verifique se a connection string está correta no `.env.local`
- Verifique se o firewall do Azure permite seu IP
- Teste a conexão com o script `testar_conexao_azure.py`

### Erro: "Prisma Client not generated"
```bash
npx prisma generate
```

## 📝 Próximos Passos

1. Testar login com usuário criado
2. Verificar redirecionamento para troca de senha
3. Implementar medidas de análise
4. Adicionar gráficos no dashboard
