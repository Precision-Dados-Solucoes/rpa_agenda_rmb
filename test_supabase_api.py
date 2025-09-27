#!/usr/bin/env python3
"""
Script para testar a conexão com o Supabase via API REST
Execute este script para verificar se as credenciais da API estão corretas
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis de ambiente
load_dotenv('config.env')

def test_supabase_api():
    """Testa a conexão com o Supabase via API"""
    print("="*70)
    print("🧪 TESTE DE CONEXÃO SUPABASE API")
    print("="*70)
    
    # Obtém as credenciais da API
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    print("🔍 VERIFICAÇÃO DE CREDENCIAIS DA API:")
    print(f"  SUPABASE_URL: {supabase_url}")
    print(f"  SUPABASE_ANON_KEY: {'*' * len(supabase_key) if supabase_key else 'NÃO CONFIGURADO'}")
    
    if not supabase_url or not supabase_key:
        print("❌ ERRO: Credenciais da API do Supabase não configuradas!")
        print("🔧 Configure SUPABASE_URL e SUPABASE_ANON_KEY no arquivo config.env")
        print("🔧 Essas credenciais estão disponíveis no painel do Supabase em Settings > API")
        return False
    
    try:
        # Criar cliente Supabase
        print("🔄 Criando cliente Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Cliente Supabase criado com sucesso!")
        
        # Teste básico de conectividade
        print("🔄 Testando conectividade...")
        result = supabase.table("agenda_base").select("count", count="exact").execute()
        
        if result.count is not None:
            print(f"✅ Conectividade OK! Registros na tabela: {result.count}")
        else:
            print("⚠️ Conectividade OK, mas não foi possível contar registros")
        
        # Teste de inserção (dados de teste)
        print("🔄 Testando inserção de dados de teste...")
        test_data = {
            "id_legalone": 999999,
            "compromisso_tarefa": "Teste API",
            "tipo": "Teste",
            "subtipo": "API",
            "etiqueta": "teste",
            "pasta_proc": "TEST",
            "numero_cnj": "0000000-00.0000.0.00.0000",
            "executante": "Sistema",
            "executante_sim": "Sim",
            "descricao": "Teste de conectividade da API",
            "status": "Ativo",
            "link": "https://teste.com"
        }
        
        # Inserir dados de teste
        insert_result = supabase.table("agenda_base").insert(test_data).execute()
        
        if insert_result.data:
            print("✅ Dados de teste inseridos com sucesso!")
            print(f"📊 ID do registro inserido: {insert_result.data[0].get('id', 'N/A')}")
            
            # Remover dados de teste
            print("🔄 Removendo dados de teste...")
            if 'id' in insert_result.data[0]:
                delete_result = supabase.table("agenda_base").delete().eq("id", insert_result.data[0]['id']).execute()
                if delete_result.data:
                    print("✅ Dados de teste removidos com sucesso!")
                else:
                    print("⚠️ Dados de teste inseridos, mas não foi possível removê-los")
        else:
            print("❌ Falha ao inserir dados de teste")
            return False
        
        print("✅ Teste de API concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar API do Supabase: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        
        # Logs específicos para diferentes tipos de erro
        if "Invalid API key" in str(e):
            print("🔐 Erro: Chave da API inválida - verifique SUPABASE_ANON_KEY")
        elif "Invalid URL" in str(e):
            print("🌐 Erro: URL inválida - verifique SUPABASE_URL")
        elif "Connection" in str(e):
            print("🌐 Erro de conexão - verifique sua internet e URL")
        elif "Permission" in str(e):
            print("🔒 Erro de permissão - verifique as políticas RLS da tabela")
        
        return False

if __name__ == "__main__":
    print("🧪 TESTE DE CONEXÃO COM SUPABASE API")
    print("=" * 70)
    
    success = test_supabase_api()
    
    print("\n" + "="*70)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ API do Supabase funcionando")
        print("✅ Inserção e remoção de dados funcionando")
        print("🚀 Pronto para usar a API no RPA!")
    else:
        print("❌ TESTE FALHOU!")
        print("🔧 Verifique as credenciais da API no arquivo config.env")
        print("🔧 Acesse o painel do Supabase em Settings > API")
    print("="*70)
