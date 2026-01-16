-- Script para atualizar permissões de usuários existentes
-- Execute este script no Azure SQL Database

-- 1. Verificar usuários sem permissões
SELECT 
    id,
    email,
    nome,
    role,
    paginas_autorizadas,
    executantes_autorizados
FROM Usuarios
WHERE paginas_autorizadas IS NULL 
   OR paginas_autorizadas = ''
   OR executantes_autorizados IS NULL
   OR executantes_autorizados = '';

-- 2. Atualizar administradores (acesso total)
UPDATE Usuarios
SET 
    paginas_autorizadas = '["dashboard_agenda", "dashboard_indicadores", "gerenciamento_usuarios"]',
    executantes_autorizados = '[]'  -- Array vazio = todos os executantes
WHERE role = 'administrador'
  AND (paginas_autorizadas IS NULL 
       OR paginas_autorizadas = ''
       OR executantes_autorizados IS NULL
       OR executantes_autorizados = '');

-- 3. Atualizar usuários não-administradores (valores padrão)
-- IMPORTANTE: Ajuste os valores conforme necessário para cada usuário
UPDATE Usuarios
SET 
    paginas_autorizadas = '["dashboard_agenda", "dashboard_indicadores"]',
    executantes_autorizados = '[]'  -- Array vazio = todos os executantes
WHERE role != 'administrador'
  AND (paginas_autorizadas IS NULL 
       OR paginas_autorizadas = ''
       OR executantes_autorizados IS NULL
       OR executantes_autorizados = '');

-- 4. Verificar resultado
SELECT 
    id,
    email,
    nome,
    role,
    paginas_autorizadas,
    executantes_autorizados
FROM Usuarios
ORDER BY nome;

PRINT 'Script executado com sucesso!';
PRINT 'IMPORTANTE: Usuários não-administradores foram atualizados com valores padrão.';
PRINT 'Edite cada usuário no sistema para definir os executantes autorizados específicos.';
