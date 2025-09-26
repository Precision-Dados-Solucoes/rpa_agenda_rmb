# 🚀 Instruções de Configuração do RPA

## ⚠️ Problema Identificado
O Playwright não está instalado no seu sistema. Vamos resolver isso!

## 🔧 Solução Passo a Passo

### 1. **Instalar Dependências**
Execute os seguintes comandos no terminal (um por vez):

```bash
pip install playwright==1.40.0
pip install pandas==2.1.4
pip install asyncpg==0.29.0
pip install python-dotenv==1.0.0
pip install openpyxl==3.1.2
```

### 2. **Instalar Navegadores do Playwright**
```bash
python -m playwright install chromium
```

### 3. **Testar Instalação**
```bash
python test_installation.py
```

### 4. **Executar RPA**
```bash
python rpa_agenda_rmb.py
```

## 🆘 Alternativa: Script Automático

Se preferir, execute o script automático:
```bash
python setup_rpa.py
```

## 📋 Verificação Manual

Para verificar se tudo está funcionando, execute:
```bash
python -c "import playwright; print('Playwright OK!')"
```

## 🎯 Próximos Passos

1. **Execute os comandos acima**
2. **Teste a instalação**
3. **Execute o RPA para inspeção**
4. **Me informe o que encontrar**

## 🔍 O que o RPA fará

- ✅ Fazer login no sistema
- ✅ Parar na tela após login
- ✅ Gerar screenshots de debug
- ✅ Manter navegador aberto para inspeção

## 📞 Precisa de Ajuda?

Se encontrar algum erro, me envie:
- A mensagem de erro completa
- O resultado do comando `python test_installation.py`
- Screenshots se necessário
