import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

// Configurar Prisma com opções de conexão mais robustas
export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['error', 'warn'] : ['error'],
  errorFormat: 'pretty',
})

// Adicionar tratamento de erro para reconexão
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

// Função helper para verificar conexão
export async function testConnection() {
  try {
    await prisma.$connect()
    return true
  } catch (error) {
    console.error('Erro ao conectar com o banco de dados:', error)
    return false
  }
}
