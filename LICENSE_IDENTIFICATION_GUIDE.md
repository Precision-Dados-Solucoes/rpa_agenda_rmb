# 🔍 Guia para Identificar a Licença Correta

## 🎯 Objetivo
Identificar a 4ª licença (robertomatos - cleiton.sanches) na tela de seleção dinâmica.

## 📋 Passo a Passo

### 1. **Execute o Script**
```bash
python rpa_agenda_rmb.py
```

### 2. **Aguarde a Página de Seleção de Licença**
- O script parará automaticamente na tela de seleção
- Você verá todas as licenças disponíveis

### 3. **Abra o DevTools**
- Pressione **F12** no navegador
- Clique na aba **"Elements"** ou **"Elementos"**

### 4. **Use a Ferramenta de Seleção**
- Clique no ícone de **seta** no canto superior esquerdo do DevTools
- Clique na **4ª licença** (robertomatos - cleiton.sanches)

### 5. **Identifique o Elemento HTML**
Procure por algo como:
```html
<input part="control" type="radio" value="valor_unico" ...>
<td data-dd-privacy="mask">robertomatos - cleiton.sanches</td>
```

## 🔍 **O que Procurar**

### **Opção 1: Atributo `value`**
```html
<input part="control" type="radio" value="VALOR_UNICO" ...>
```
**Seletor:** `input[value="VALOR_UNICO"]`

### **Opção 2: Atributo `current-value`**
```html
<saf-radio current-value="VALOR_UNICO">
```
**Seletor:** `saf-radio[current-value="VALOR_UNICO"]`

### **Opção 3: Por Texto**
```html
<td data-dd-privacy="mask">robertomatos - cleiton.sanches</td>
```
**Seletor:** `td:has-text("robertomatos - cleiton.sanches")`

### **Opção 4: Por Posição (4ª licença)**
```css
/* 4ª licença */
saf-radio:nth-child(4) input[part="control"]
```

## 📝 **O que Me Informar**

Me envie **UM** dos seguintes:

1. **Seletor CSS completo:**
   ```
   input[value="valor_especifico"]
   ```

2. **Valor do atributo:**
   ```
   value="abc123def456"
   ```

3. **Estrutura HTML completa:**
   ```html
   <input part="control" type="radio" value="..." ...>
   ```

4. **Posição na lista:**
   ```
   4ª licença da lista
   ```

## 💡 **Dicas Importantes**

- ✅ A tela é **dinâmica** (pode ter 3, 4, 5... licenças)
- ✅ Procure por **"robertomatos"** no HTML
- ✅ Verifique se há um **valor único** no input
- ✅ Observe a **estrutura HTML completa**
- ✅ Teste o seletor no **Console do DevTools**

## 🧪 **Teste do Seletor**

No Console do DevTools, teste:
```javascript
// Substitua "SEU_SELETOR" pelo seletor encontrado
document.querySelector("SEU_SELETOR")
```

Se retornar o elemento correto, o seletor está certo!

## 🚀 **Próximos Passos**

1. Execute o script
2. Siga este guia
3. Me informe o seletor correto
4. Eu atualizarei o script automaticamente
