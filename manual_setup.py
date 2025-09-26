#!/usr/bin/env python3
"""
Script para configurar manualmente o ambiente RPA
"""

import subprocess
import sys
import os

def install_package(package):
    """Instala um pacote usando pip"""
    try:
        print(f"🔄 Instalando {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {package} instalado com sucesso!")
            return True
        else:
            print(f"   ❌ Erro ao instalar {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Exceção ao instalar {package}: {e}")
        return False

def main():
    print("🚀 Configuração Manual do RPA")
    print("=" * 50)
    
    # Lista de pacotes para instalar
    packages = [
        "playwright",
        "pandas", 
        "asyncpg",
        "python-dotenv",
        "openpyxl"
    ]
    
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"📊 Resultado: {success_count}/{len(packages)} pacotes instalados")
    
    if success_count == len(packages):
        print("🎉 Todos os pacotes instalados!")
        print("\n🔄 Agora instalando navegadores do Playwright...")
        
        try:
            result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Navegador Chromium instalado!")
            else:
                print(f"   ❌ Erro ao instalar navegador: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Exceção ao instalar navegador: {e}")
        
        print("\n🧪 Testando instalação...")
        try:
            from playwright.async_api import async_playwright
            print("   ✅ Playwright importado com sucesso!")
        except ImportError as e:
            print(f"   ❌ Erro ao importar Playwright: {e}")
        
        print("\n🎯 Próximo passo: Execute 'python rpa_agenda_rmb.py'")
    else:
        print("⚠️  Alguns pacotes falharam. Tente instalar manualmente:")
        for package in packages:
            print(f"   pip install {package}")

if __name__ == "__main__":
    main()
