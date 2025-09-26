#!/usr/bin/env python3
"""
Script para testar se todas as dependências estão instaladas corretamente
"""

def test_imports():
    """Testa se todos os módulos necessários podem ser importados"""
    try:
        print("🔍 Testando importações...")
        
        print("  - playwright...")
        from playwright.async_api import async_playwright, TimeoutError
        print("    ✅ playwright importado com sucesso")
        
        print("  - pandas...")
        import pandas as pd
        print("    ✅ pandas importado com sucesso")
        
        print("  - asyncpg...")
        import asyncpg
        print("    ✅ asyncpg importado com sucesso")
        
        print("  - dotenv...")
        from dotenv import load_dotenv
        print("    ✅ dotenv importado com sucesso")
        
        print("  - openpyxl...")
        import openpyxl
        print("    ✅ openpyxl importado com sucesso")
        
        print("\n🎉 Todas as dependências estão instaladas!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Erro ao importar: {e}")
        print("\n💡 Execute o seguinte comando para instalar as dependências:")
        print("   pip install playwright pandas asyncpg python-dotenv openpyxl")
        return False

def test_playwright_browsers():
    """Testa se os navegadores do Playwright estão instalados"""
    try:
        print("\n🔍 Testando navegadores do Playwright...")
        
        import asyncio
        from playwright.async_api import async_playwright
        
        async def test_browser():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://www.google.com")
                title = await page.title()
                await browser.close()
                return title
        
        result = asyncio.run(test_browser())
        print(f"    ✅ Navegador funcionando! Título da página: {result}")
        return True
        
    except Exception as e:
        print(f"    ❌ Erro ao testar navegador: {e}")
        print("\n💡 Execute o seguinte comando para instalar os navegadores:")
        print("   python -m playwright install chromium")
        return False

if __name__ == "__main__":
    print("🚀 Testando instalação do RPA...")
    print("=" * 50)
    
    # Testa importações
    imports_ok = test_imports()
    
    if imports_ok:
        # Testa navegadores
        browsers_ok = test_playwright_browsers()
        
        if browsers_ok:
            print("\n🎉 Tudo funcionando! Você pode executar o RPA agora.")
            print("   Execute: python rpa_agenda_rmb.py")
        else:
            print("\n⚠️  Dependências instaladas, mas navegadores não funcionando.")
    else:
        print("\n❌ Algumas dependências não estão instaladas.")
    
    print("\n" + "=" * 50)
