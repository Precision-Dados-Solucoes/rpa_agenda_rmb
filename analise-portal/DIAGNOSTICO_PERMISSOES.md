# Diagnóstico de Problemas de Permissões

## Passo 1: Verificar se o usuário tem permissões no banco

Execute no Azure SQL Database:

```sql
SELECT 
    id,
    email,
    nome,
    role,
    paginas_autorizadas,
    executantes_autorizados
FROM Usuarios
WHERE email = 'EMAIL_DO_USUARIO_AQUI';
```

**Se os campos `paginas_autorizadas` ou `executantes_autorizados` estiverem NULL ou vazios:**
- Execute o script `atualizar_permissoes_usuarios_existentes.sql`
- Ou edite o usuário no sistema para definir as permissões

## Passo 2: Verificar se o login está retornando permissões

1. Abra o console do navegador (F12)
2. Faça logout e login novamente
3. No console, execute:

```javascript
const user = JSON.parse(localStorage.getItem('user'));
console.log('Usuário no localStorage:', user);
console.log('Páginas autorizadas:', user?.paginas_autorizadas);
console.log('Executantes autorizados:', user?.executantes_autorizados);
```

**Se não aparecer `paginas_autorizadas` ou `executantes_autorizados`:**
- O problema está no login. Verifique os logs do Vercel.

## Passo 3: Testar endpoint de debug

No console do navegador, execute:

```javascript
const token = localStorage.getItem('token');
fetch('/api/debug/permissoes', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => console.log('Debug permissões:', data));
```

Isso mostrará:
- Se o token é válido
- Quais permissões estão sendo obtidas do banco
- Se há algum erro

## Passo 4: Verificar logs do Vercel

1. Acesse o dashboard do Vercel
2. Vá em "Deployments" > Selecione o último deploy > "Functions"
3. Procure por logs que começam com `[DEBUG permissoes]` ou `[DEBUG construirWherePermissoes]`

Isso mostrará:
- Se o token está sendo recebido
- Quais permissões estão sendo obtidas
- Como o filtro está sendo aplicado

## Problemas Comuns

### 1. Usuário não tem permissões no banco
**Solução:** Execute `atualizar_permissoes_usuarios_existentes.sql`

### 2. Login não está retornando permissões
**Solução:** Verifique se o código foi atualizado no Vercel. Faça um novo deploy se necessário.

### 3. Token não está sendo enviado nas requisições
**Solução:** Verifique o console do navegador. Todas as requisições devem ter o header `Authorization: Bearer <token>`

### 4. Array vazio de executantes = acesso a todos
**Comportamento esperado:** Se `executantes_autorizados = []` (array vazio), o usuário vê TODOS os executantes. Para restringir, o array deve conter os nomes dos executantes permitidos.

## Exemplo de Configuração Correta

Para um usuário que deve ver apenas "Marcus Zago de Brito" e "Ana Clara dos Santos":

```sql
UPDATE Usuarios
SET 
    paginas_autorizadas = '["dashboard_agenda", "dashboard_indicadores"]',
    executantes_autorizados = '["Marcus Zago de Brito", "Ana Clara dos Santos"]'
WHERE email = 'email@exemplo.com';
```
