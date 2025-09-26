#!/usr/bin/env python3
"""
Script para configurar o ambiente RPA
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Executa um comando e retorna o resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} - Sucesso!")
            return True
        else:
            print(f"   ❌ {description} - Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ {description} - Exceção: {e}")
        return False

def main():
    print("🚀 Configurando ambiente RPA...")
    print("=" * 50)
    
    # Lista de comandos para executar
    commands = [
        ("pip install playwright==1.40.0", "Instalando Playwright"),
        ("pip install pandas==2.1.4", "Instalando Pandas"),
        ("pip install asyncpg==0.29.0", "Instalando AsyncPG"),
        ("pip install python-dotenv==1.0.0", "Instalando python-dotenv"),
        ("pip install openpyxl==3.1.2", "Instalando openpyxl"),
        ("python -m playwright install chromium", "Instalando navegador Chromium"),
    ]
    
    success_count = 0
    total_commands = len(commands)
    
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
        print()  # Linha em branco
    
    print("=" * 50)
    print(f"📊 Resultado: {success_count}/{total_commands} comandos executados com sucesso")
    
    if success_count == total_commands:
        print("🎉 Ambiente configurado com sucesso!")
        print("   Agora você pode executar: python rpa_agenda_rmb.py")
    else:
        print("⚠️  Alguns comandos falharam. Verifique os erros acima.")
        print("   Tente executar os comandos manualmente no terminal.")
    
    print("\n💡 Para testar se tudo está funcionando, execute:")
    print("   python test_installation.py")

if __name__ == "__main__":
    main()
