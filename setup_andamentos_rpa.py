#!/usr/bin/env python3
"""
Script de configuração para RPA Andamentos
Verifica dependências e configura o ambiente
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário. Versão atual:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_requirements():
    """Instala as dependências necessárias"""
    print("📦 Instalando dependências...")
    
    try:
        # Instalar requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_andamentos.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependências Python instaladas")
        
        # Instalar playwright browsers
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True, text=True)
        print("✅ Navegador Chromium instalado")
        
        # Instalar dependências do sistema (Linux)
        if platform.system() == "Linux":
            subprocess.run(["playwright", "install-deps", "chromium"], 
                          check=True, capture_output=True, text=True)
            print("✅ Dependências do sistema instaladas")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def check_environment_file():
    """Verifica se o arquivo de configuração existe"""
    config_file = "config.env"
    
    if not os.path.exists(config_file):
        print(f"⚠️ Arquivo {config_file} não encontrado")
        print("📝 Criando arquivo de exemplo...")
        
        example_content = """# Configurações do RPA Andamentos
# Copie este arquivo e preencha com suas credenciais

# Credenciais Novajus
NOVAJUS_USERNAME=seu_email@exemplo.com
NOVAJUS_PASSWORD=sua_senha

# Credenciais Supabase
SUPABASE_HOST=db.exemplo.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua_senha_supabase
"""
        
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(example_content)
        
        print(f"✅ Arquivo {config_file} criado com exemplo")
        print("🔧 Configure suas credenciais no arquivo antes de executar")
        return False
    else:
        print(f"✅ Arquivo {config_file} encontrado")
        return True

def create_directories():
    """Cria diretórios necessários"""
    directories = ["downloads", ".github/workflows"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Diretório criado: {directory}")
        else:
            print(f"✅ Diretório existe: {directory}")

def show_schedule_info():
    """Mostra informações sobre o agendamento"""
    print("\n" + "="*60)
    print("📅 AGENDAMENTO AUTOMÁTICO")
    print("="*60)
    print("🕐 Horários de execução:")
    print("   • Segunda a Sexta: 12:00 BRT")
    print("   • Segunda a Sexta: 17:00 BRT")
    print("")
    print("🌍 Fuso horário: São Paulo (BRT)")
    print("🔄 Execução: GitHub Actions")
    print("")
    print("📋 Tabela de destino: andamento_base")
    print("🔍 Comparação: id_andamento_legalone ↔ id_andamento")
    print("⚙️ Operação: UPSERT (atualiza se existe, insere se novo)")
    print("="*60)

def main():
    """Função principal de configuração"""
    print("🔧 CONFIGURAÇÃO DO RPA ANDAMENTOS")
    print("="*50)
    
    # Verificações
    checks = [
        ("Versão do Python", check_python_version),
        ("Arquivo de configuração", check_environment_file),
        ("Dependências", install_requirements),
    ]
    
    # Criar diretórios
    create_directories()
    
    # Executar verificações
    all_ok = True
    for name, check_func in checks:
        print(f"\n🔍 Verificando {name}...")
        if not check_func():
            all_ok = False
    
    # Resultado final
    print("\n" + "="*50)
    if all_ok:
        print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("🚀 O RPA está pronto para ser executado")
        print("\n📝 Para executar manualmente:")
        print("   python rpa_andamentos_completo.py")
        print("\n📅 Para agendamento automático:")
        print("   Configure os secrets no GitHub e faça push do código")
    else:
        print("⚠️ CONFIGURAÇÃO INCOMPLETA")
        print("🔧 Verifique os itens marcados com ❌ acima")
        print("📝 Configure suas credenciais no arquivo config.env")
    
    show_schedule_info()

if __name__ == "__main__":
    main()
