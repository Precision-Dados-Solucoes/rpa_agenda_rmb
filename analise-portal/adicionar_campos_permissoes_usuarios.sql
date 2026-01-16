-- Adicionar campos de permissões na tabela Usuarios
-- páginas_autorizadas: JSON com array de páginas permitidas
-- executantes_autorizados: JSON com array de executantes permitidos

-- Adicionar coluna páginas_autorizadas
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('Usuarios') 
    AND name = 'paginas_autorizadas'
)
BEGIN
    ALTER TABLE Usuarios
    ADD paginas_autorizadas NVARCHAR(MAX) NULL;
    PRINT 'Coluna paginas_autorizadas adicionada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Coluna paginas_autorizadas já existe.';
END
GO

-- Adicionar coluna executantes_autorizados
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('Usuarios') 
    AND name = 'executantes_autorizados'
)
BEGIN
    ALTER TABLE Usuarios
    ADD executantes_autorizados NVARCHAR(MAX) NULL;
    PRINT 'Coluna executantes_autorizados adicionada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Coluna executantes_autorizados já existe.';
END
GO

-- Para administradores, definir acesso total (todas as páginas e todos os executantes)
UPDATE Usuarios
SET paginas_autorizadas = '["dashboard_agenda", "dashboard_indicadores", "gerenciamento_usuarios"]',
    executantes_autorizados = '[]' -- Array vazio significa todos os executantes
WHERE role = 'administrador'
AND (paginas_autorizadas IS NULL OR executantes_autorizados IS NULL);
GO

PRINT 'Script executado com sucesso!';
