# Portal de Análise de Dados

Sistema web para análise de dados com autenticação multi-tenant.

## 🚀 Tecnologias

- **Next.js 15** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **Prisma** (ORM)
- **Azure SQL Database**
- **JWT** (Autenticação)

## 📋 Pré-requisitos

- Node.js 18+ 
- npm ou yarn
- Azure SQL Database configurado

## 🔧 Instalação

```bash
# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
# Editar .env.local com suas credenciais

# Configurar Prisma
npx prisma generate
npx prisma db pull  # Puxar schema do banco existente

# Executar em desenvolvimento
npm run dev
```

## 🔐 Autenticação

- **Login**: `/login`
- **Troca de Senha**: `/trocar-senha` (primeiro acesso)
- **Dashboard**: `/dashboard` (protegido)

## 📁 Estrutura

```
app/
├── (auth)/          # Rotas de autenticação
├── (dashboard)/     # Rotas protegidas
└── api/             # API routes

components/
├── ui/              # Componentes shadcn
└── auth/            # Componentes de autenticação

lib/
├── prisma.ts        # Cliente Prisma
└── auth.ts          # Helpers de autenticação
```
