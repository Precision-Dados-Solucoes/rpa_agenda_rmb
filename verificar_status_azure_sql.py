"""
Script para verificar o status do banco Azure SQL e tentar reconectar
"""

import os
import time
from dotenv import load_dotenv
from azure_sql_helper import get_azure_connection

load_dotenv('config.env')

def verificar_status():
    """Verifica o status do banco Azure SQL"""
    print("=" * 70)
    print("VERIFICANDO STATUS DO BANCO AZURE SQL")
    print("=" * 70)
    print()
    
    server = os.getenv("AZURE_SERVER")
    database = os.getenv("AZURE_DATABASE")
    
    print(f"Servidor: {server}")
    print(f"Banco: {database}")
    print()
    
    # Tentar conectar várias vezes
    max_tentativas = 5
    intervalo = 10  # segundos
    
    for tentativa in range(1, max_tentativas + 1):
        print(f"Tentativa {tentativa}/{max_tentativas}...")
        
        try:
            conn = get_azure_connection()
            
            if conn:
                print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
                print()
                
                # Verificar última atualização
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        MAX(created_at) as ultima_atualizacao,
                        COUNT(*) as total_registros
                    FROM agenda_base
                """)
                
                result = cursor.fetchone()
                if result:
                    ultima_atualizacao = result[0]
                    total_registros = result[1]
                    
                    print(f"Total de registros: {total_registros:,}")
                    if ultima_atualizacao:
                        print(f"Última atualização: {ultima_atualizacao}")
                
                conn.close()
                return True
            else:
                print(f"❌ Falha na tentativa {tentativa}")
                
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa}: {e}")
        
        if tentativa < max_tentativas:
            print(f"Aguardando {intervalo} segundos antes da próxima tentativa...")
            time.sleep(intervalo)
        print()
    
    print("=" * 70)
    print("❌ NÃO FOI POSSÍVEL CONECTAR APÓS {max_tentativas} TENTATIVAS")
    print("=" * 70)
    print()
    print("POSSÍVEIS CAUSAS:")
    print("1. Banco Azure SQL está PAUSADO (modo econômico)")
    print("2. Banco está temporariamente INDISPONÍVEL")
    print("3. Firewall bloqueando a conexão")
    print("4. Problema de rede/conectividade")
    print()
    print("AÇÕES RECOMENDADAS:")
    print("1. Acesse o Portal Azure: https://portal.azure.com")
    print("2. Navegue até: SQL Databases → dbAdvromas")
    print("3. Verifique se o banco está pausado")
    print("4. Se estiver pausado, clique em 'Resume' (Retomar)")
    print("5. Aguarde alguns minutos e tente novamente")
    print()
    
    return False

if __name__ == "__main__":
    verificar_status()
