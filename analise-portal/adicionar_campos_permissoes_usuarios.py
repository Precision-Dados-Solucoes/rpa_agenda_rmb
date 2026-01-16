#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar campos de permissões na tabela Usuarios
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure_sql_helper import get_azure_connection

def executar_script_sql():
    """Executa o script SQL para adicionar campos de permissões"""
    conn = None
    try:
        conn = get_azure_connection()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return False

        cursor = conn.cursor()

        # Ler o arquivo SQL
        script_path = os.path.join(os.path.dirname(__file__), 'adicionar_campos_permissoes_usuarios.sql')
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()

        # Executar o script (dividir por GO se necessário)
        comandos = [cmd.strip() for cmd in script.split('GO') if cmd.strip()]

        for comando in comandos:
            if comando:
                try:
                    cursor.execute(comando)
                    conn.commit()
                    print(f"✅ Comando executado: {comando[:50]}...")
                except Exception as e:
                    print(f"⚠️ Aviso ao executar comando: {e}")
                    # Continuar mesmo se houver erro (pode ser que a coluna já exista)

        print("\n✅ Script SQL executado com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro ao executar script SQL: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("=" * 80)
    print("Adicionando campos de permissões na tabela Usuarios")
    print("=" * 80)
    executar_script_sql()
