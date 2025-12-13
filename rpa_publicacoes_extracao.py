#!/usr/bin/env python3
"""
RPA para Extração de Publicações
Automatiza a extração do relatório de publicações do Legal One/Novajus
URL: https://robertomatos.novajus.com.br/processos/GenericReport/?id=678
Arquivo esperado: z-rpa-publicacoes.xlsx (ou similar)
Processamento: INSERT na tabela tb_publicacoes
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv
from pathlib import Path
from azure_sql_helper import insert_publicacoes

# Carrega as variáveis de ambiente do arquivo config.env
load_dotenv('config.env')

# --- Configuração da pasta de downloads ---
downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
print(f"A pasta de downloads será: {os.path.abspath(downloads_dir)}")

async def close_any_known_popup(page):
    """
    Tenta fechar popups modais ou overlays usando seletores comuns para botões de fechar.
    Retorna True se um popup foi encontrado e tentado fechar, False caso contrário.
    """
    close_selectors = [
        '[aria-label="Close"]',
        'button:has-text("Fechar")',
        'button:has-text("OK")',
        'button.close',
        '.modal-footer button:has-text("Fechar")',
        '.modal-header button.close',
        '.popup-close',
        '#close-button',
        '[role="dialog"] button:has-text("Fechar")'
    ]

    print("Tentando fechar popups (se houver)...")
    for selector in close_selectors:
        try:
            element = page.locator(selector)
            if await element.is_visible(timeout=1000):
                print(f"  Popup detectado com seletor: {selector}. Tentando fechar...")
                await element.click(timeout=3000)
                print(f"  Popup fechado com sucesso usando seletor: {selector}.")
                await page.wait_for_timeout(500)
                return True
        except TimeoutError:
            pass
        except Exception as e:
            print(f"  Erro inesperado ao tentar fechar popup com seletor {selector}: {e}")
            pass
    print("Nenhum popup conhecido encontrado ou fechado.")
    return False

def read_excel_file(file_path):
    """
    Lê um arquivo Excel e retorna um DataFrame do pandas.
    """
    print(f"Lendo o arquivo: {file_path}")
    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, forneça um arquivo .xlsx ou .csv")
        
        print(f"Arquivo '{file_path}' lido com sucesso.")
        print(f"Total de linhas: {len(df)}")
        print(f"Colunas do DataFrame: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None

def processar_dados_publicacoes(df):
    """
    Processa os dados do DataFrame de publicações, separando data/hora das colunas datetime.
    """
    print("\n🔄 Processando dados de publicações...")
    print("="*70)
    
    # Criar novo DataFrame processado
    df_processed = pd.DataFrame()
    
    # Separar "Data/hora cadastro" em data_cadastro e hora_cadastro
    if 'Data/hora cadastro' in df.columns:
        print("📅 Processando coluna 'Data/hora cadastro'...")
        df_processed['data_cadastro'] = df['Data/hora cadastro'].apply(lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None)
        df_processed['hora_cadastro'] = df['Data/hora cadastro'].apply(lambda x: x.time() if pd.notna(x) and hasattr(x, 'time') else None)
        print("✅ 'Data/hora cadastro' → 'data_cadastro' e 'hora_cadastro'")
    else:
        print("⚠️ Coluna 'Data/hora cadastro' não encontrada")
        df_processed['data_cadastro'] = None
        df_processed['hora_cadastro'] = None
    
    # Separar "Data/hora" em data_publicacao e hora_publicacao
    if 'Data/hora' in df.columns:
        print("📅 Processando coluna 'Data/hora'...")
        df_processed['data_publicacao'] = df['Data/hora'].apply(lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None)
        df_processed['hora_publicacao'] = df['Data/hora'].apply(lambda x: x.time() if pd.notna(x) and hasattr(x, 'time') else None)
        print("✅ 'Data/hora' → 'data_publicacao' e 'hora_publicacao'")
    else:
        print("⚠️ Coluna 'Data/hora' não encontrada")
        df_processed['data_publicacao'] = None
        df_processed['hora_publicacao'] = None
    
    # Copiar colunas restantes
    colunas_restantes = {
        'Pasta': 'pasta',
        'Número de CNJ': 'numero_cnj',
        'Tratamento': 'tratamento',
        'Publicação': 'publicacao'
    }
    
    for col_original, col_nova in colunas_restantes.items():
        if col_original in df.columns:
            df_processed[col_nova] = df[col_original]
            print(f"✅ '{col_original}' → '{col_nova}'")
        else:
            print(f"⚠️ Coluna '{col_original}' não encontrada")
            df_processed[col_nova] = None
    
    print(f"\n✅ Processamento concluído!")
    print(f"📊 Total de registros processados: {len(df_processed)}")
    
    return df_processed

async def inserir_dados_supabase(df, table_name="tb_publicacoes"):
    """
    Insere os dados processados na tabela do Supabase.
    """
    print(f"\n🔗 Conectando ao Supabase...")
    print("="*70)
    
    # Obter credenciais do config.env (mesmo padrão dos outros scripts)
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Tentar construir a connection string a partir de variáveis individuais
        # Mesmo padrão do rpa_agenda_rmb.py
        host = os.getenv("host") or os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
        port = os.getenv("port") or os.getenv("SUPABASE_PORT", "5432")
        database = os.getenv("dbname") or os.getenv("SUPABASE_DATABASE", "postgres")
        user = os.getenv("user") or os.getenv("SUPABASE_USER", "postgres")
        password = os.getenv("password") or os.getenv("SUPABASE_PASSWORD")
        
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=int(port),
                database=database,
                ssl="require"
            )
        except Exception as e:
            print(f"❌ Erro ao conectar com credenciais individuais: {e}")
            return False
    else:
        try:
            conn = await asyncpg.connect(database_url)
        except Exception as e:
            print(f"❌ Erro ao conectar com connection string: {e}")
            return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Verificar se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"❌ ERRO: Tabela '{table_name}' não existe!")
            return False
        
        print(f"✅ Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"📊 Registros existentes: {count_before}")
        
        # Preparar colunas para inserção
        columns_df = df.columns.tolist()
        columns_sql = ", ".join(f'"{col}"' for col in columns_df)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
        
        print(f"\n📊 Inserindo {len(df)} registros...")
        print("="*70)
        
        inserted_count = 0
        
        async with conn.transaction():
            for index, row in df.iterrows():
                try:
                    # Preparar valores
                    values = []
                    for col in columns_df:
                        value = row[col]
                        # Tratar valores NaN/None
                        if pd.isna(value):
                            values.append(None)
                        else:
                            values.append(value)
                    
                    # Inserir registro
                    await conn.execute(insert_query, *values)
                    inserted_count += 1
                    
                    if (index + 1) % 10 == 0:
                        print(f"✅ {inserted_count} registros inseridos...")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao inserir linha {index + 1}: {e}")
                    continue
        
        # Verificar resultado
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"\n✅ Inserção concluída!")
        print(f"📊 Registros inseridos: {inserted_count}")
        print(f"📊 Total na tabela: {count_before} → {count_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()
        print("🔌 Conexão fechada.")

async def run():
    browser = None
    try:
        async with async_playwright() as p:
            # Configuração automática do modo headless
            # Modo headless para execução normal (sem interface gráfica)
            headless_mode = True  # Executar sem interface gráfica
            
            # Se estiver em ambiente CI/CD (GitHub Actions), força headless
            if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
                headless_mode = True
                
            print("="*70)
            print(f"🚀 INICIANDO RPA DE PUBLICAÇÕES")
            print(f"📺 Modo: {'headless' if headless_mode else 'COM INTERFACE GRÁFICA (VISÍVEL)'}")
            print("="*70)
            browser = await p.chromium.launch(headless=headless_mode)  # Sem slow_mo para execução mais rápida
            
            chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" 
            
            # Configurar contexto com cookies e JavaScript habilitados
            context = await browser.new_context(
                user_agent=chrome_user_agent,
                accept_downloads=True,
                java_script_enabled=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Aceitar cookies automaticamente
            await context.add_cookies([])  # Preparar para cookies
            
            page = await context.new_page()

            # --- CREDENCIAIS DE LOGIN NO SISTEMA NOVAJUS ---
            USERNAME = os.getenv("NOVAJUS_USERNAME", "cleiton.sanches@precisionsolucoes.com")
            PASSWORD = os.getenv("NOVAJUS_PASSWORD", "PDS2025@")

            # --- ETAPA 1: NAVEGAR PARA A PÁGINA DE LOGIN ---
            novajus_login_url = "https://login.novajus.com.br/conta/login" 
            print("\n" + "="*70)
            print("📍 ETAPA 1: NAVEGANDO PARA PÁGINA DE LOGIN")
            print("="*70)
            print(f"🌐 URL: {novajus_login_url}")
            
            try:
                await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=60000) 
                print(f"✅ Página carregada!")
                print(f"📍 URL atual: {page.url}")
                await page.screenshot(path="debug_initial_page.png", full_page=True)
                print("📸 Screenshot salvo: debug_initial_page.png")
            except TimeoutError:
                print(f"Erro FATAL: page.goto() para {novajus_login_url} excedeu o tempo limite. Verifique sua conexão ou a URL.")
                return
            except Exception as e:
                print(f"Erro inesperado ao navegar para a página de login: {e}")
                return

            # --- LÓGICA PARA CLICAR NO BOTÃO ONEPASS (SE PRESENTE) ---
            onepass_selector = '#btn-login-onepass' 
            print(f"Verificando e clicando no botão OnePass '{onepass_selector}' se presente...")
            try:
                onepass_button = page.locator(onepass_selector)
                if await onepass_button.is_visible(timeout=5000): 
                    print("Botão OnePass detectado. Clicando...")
                    await onepass_button.click()
                    await page.wait_for_load_state("domcontentloaded") 
                    await page.wait_for_timeout(1000)
                    print("Clicou em OnePass. Aguardando a tela de login principal.")
                    await page.screenshot(path="debug_after_onepass_click.png", full_page=True)
                else:
                    print("Botão OnePass não visível. Prosseguindo.")
            except TimeoutError:
                print("Botão OnePass não encontrado no tempo esperado. Assumindo que já está na tela principal.")
            except Exception as e:
                print(f"Erro ao lidar com o botão OnePass: {e}")

            # --- ETAPA 2: INSERIR E-MAIL ---
            print("\n" + "="*70)
            print("📍 ETAPA 2: INSERINDO E-MAIL")
            print("="*70)
            print("⏳ Aguardando campo de e-mail '#Username' aparecer...")
            try:
                await page.wait_for_selector('#Username', state='visible', timeout=30000)
                print(f"✅ Campo encontrado! Preenchendo e-mail: {USERNAME}")
                await page.fill('#Username', USERNAME)
                
                await page.keyboard.press('Tab') 
                print("Pressionado TAB após preencher o e-mail. Aguardando a tela de senha mudar...")
                
                await page.wait_for_selector('#password', state='visible', timeout=30000) 
                print("Nova tela de senha com ID '#password' detectada.")
                await page.screenshot(path="debug_after_username_fill.png", full_page=True)
                
            except TimeoutError:
                print("Erro FATAL: Campo de e-mail '#Username' ou transição para senha não ocorreu no tempo esperado.")
                await page.screenshot(path="debug_username_or_transition_error.png", full_page=True)
                return
            except Exception as e:
                print(f"Erro inesperado ao preencher e-mail e aguardar transição: {e}")
                await page.screenshot(path="debug_username_fill_error.png", full_page=True)
                return

            # --- ETAPA 3: INSERIR SENHA E CLICAR NO BOTÃO FINAL DE LOGIN ---
            print("\n" + "="*70)
            print("📍 ETAPA 3: INSERINDO SENHA E FAZENDO LOGIN")
            print("="*70)
            print("🔐 Preenchendo senha...")
            try:
                await page.fill('#password', PASSWORD)
                print("✅ Senha preenchida.")

                login_button_selector = 'button._button-login-password'
                print(f"Clicando no botão 'Entrar' final '{login_button_selector}'...")
                await page.wait_for_selector(login_button_selector, state='visible', timeout=30000)
                await page.click(login_button_selector)
                print("Botão 'Entrar' final clicado.")

                print("Aguardando o carregamento completo da página após o login...")
                try:
                    await page.wait_for_load_state("load", timeout=30000)
                except Exception as e:
                    print(f"⚠️ Timeout ao aguardar 'load', continuando mesmo assim: {e}")
                await page.wait_for_timeout(2000)
                
                await page.screenshot(path="debug_after_final_login_click.png", full_page=True)
                print("DEBUG: Captura de tela 'debug_after_final_login_click.png' tirada após o login.")
                print(f"DEBUG: URL atual após login: {page.url}")

            except TimeoutError:
                print("Erro FATAL: Campo de senha '#password' ou botão de login final não apareceu/clicável no tempo esperado OU a página após o login não carregou totalmente.")
                await page.screenshot(path="debug_password_field_or_final_button_missing.png", full_page=True)
                return
            except Exception as e:
                print(f"Erro inesperado ao preencher senha ou clicar no botão final: {e}")
                await page.screenshot(path="debug_password_fill_or_final_click_error.png", full_page=True)
                return

            await close_any_known_popup(page)

            # --- ETAPA 4: SELEÇÃO DA NOVA LICENÇA ---
            print("Aguardando página de seleção de licença carregar...")
            await page.wait_for_timeout(3000)
            
            # Tira screenshot da página de seleção de licença
            await page.screenshot(path="debug_license_selection_page.png", full_page=True)
            print("📸 Screenshot da página de seleção de licença salvo: debug_license_selection_page.png")

            # --- SELEÇÃO DA LICENÇA CORRETA USANDO CURRENT-VALUE ---
            print("Selecionando a licença usando current-value...")
            try:
                # Valor específico da licença (robertomatos - cleiton.sanches)
                # ATUALIZADO: current-value mudou para 321230142ac9f01183ce12fc83a1b95d
                license_specific_value = "321230142ac9f01183ce12fc83a1b95d"
                
                # Seletor para o saf-radio com o current-value específico
                license_selector = f'saf-radio[current-value="{license_specific_value}"] >> input[part="control"]'
                
                print(f"🎯 Valor da licença: {license_specific_value}")
                print(f"🎯 Seletor: {license_selector}")
                print("Aguardando e clicando na licença específica...")
                
                # Aguarda o elemento estar visível
                await page.wait_for_selector(license_selector, state='visible', timeout=30000)
                
                # Verificar se encontrou apenas um elemento (garantir que é o correto)
                element_count = await page.locator(license_selector).count()
                if element_count > 1:
                    print(f"⚠️  AVISO: Encontrados {element_count} elementos com o seletor. Usando o primeiro.")
                
                # Verificar o current-value antes de clicar para garantir que é o correto
                found_radio = page.locator(license_selector).first
                parent_radio = page.locator(f'saf-radio[current-value="{license_specific_value}"]').first
                actual_value = await parent_radio.get_attribute('current-value')
                
                if actual_value != license_specific_value:
                    print(f"❌ ERRO: Licença encontrada tem current-value diferente!")
                    print(f"   Esperado: {license_specific_value}")
                    print(f"   Encontrado: {actual_value}")
                    await page.screenshot(path="debug_license_wrong_value.png", full_page=True)
                    return
                
                # Clica na licença específica
                await page.click(license_selector)
                print("✅ Licença 'robertomatos - cleiton.sanches' selecionada com sucesso!")

            except TimeoutError:
                print(f"❌ Erro: Licença com current-value '{license_specific_value}' não encontrada.")
                await page.screenshot(path="debug_license_current_value_not_found.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_license_current_value_not_found.png")
                print("🔍 Verifique se a licença está visível na página.")
                return
            except Exception as e:
                print(f"❌ Erro inesperado ao selecionar a licença: {e}")
                await page.screenshot(path="debug_license_current_value_error.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_license_current_value_error.png")
                return

            await close_any_known_popup(page)

            # Clicar no botão 'Continuar' após selecionar a licença
            print("Clicando no botão 'Continuar' após selecionar a licença...")
            try:
                continue_button_selector = 'saf-button.PersonaSelectionPage-button[type="submit"]' 
                await page.wait_for_selector(continue_button_selector, state='visible', timeout=30000)
                await page.click(continue_button_selector)
                print("✅ Botão 'Continuar' clicado com sucesso!")

            except TimeoutError:
                print(f"❌ Erro: Botão 'Continuar' não encontrado.")
                await page.screenshot(path="debug_continue_button_not_found.png", full_page=True)
                return
            except Exception as e:
                print(f"❌ Erro inesperado ao clicar no botão continuar: {e}")
                await page.screenshot(path="debug_continue_button_error.png", full_page=True)
                return

            await close_any_known_popup(page)

            # --- ETAPA 5: ESPERA DA PÁGINA PÓS-LOGIN COMPLETO ---
            print("Aguardando a página inicial do sistema carregar...")
            try:
                await page.wait_for_load_state("load", timeout=30000)
            except Exception as e:
                print(f"⚠️ Timeout ao aguardar 'load', continuando mesmo assim: {e}")
            await page.wait_for_timeout(2000)

            print(f"📍 URL atual após login completo: {page.url}")
            await page.screenshot(path="debug_post_login_page.png", full_page=True)
            print("📸 Screenshot da página pós-login salvo: debug_post_login_page.png")

            await close_any_known_popup(page)

            # --- ETAPA 6: NAVEGAR PARA O RELATÓRIO DE PUBLICAÇÕES ---
            # URL diferente: /processos/ ao invés de /agenda/
            report_url = "https://robertomatos.novajus.com.br/processos/GenericReport/?id=678"
            print(f"Navegando para o relatório de publicações: {report_url}...")
            try:
                await page.goto(report_url, wait_until="domcontentloaded", timeout=60000)
                print(f"📍 URL atual após navegar para o relatório: {page.url}")
                await page.wait_for_timeout(3000)
                await page.screenshot(path="debug_report_page_loaded.png", full_page=True)
                print("📸 Screenshot da página do relatório salvo: debug_report_page_loaded.png")
            except TimeoutError:
                print(f"❌ Erro: Página do relatório não carregou no tempo esperado.")
                await page.screenshot(path="debug_report_page_load_error.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_report_page_load_error.png")
                return
            except Exception as e:
                print(f"❌ Erro inesperado ao navegar para o relatório: {e}")
                await page.screenshot(path="debug_report_page_error.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_report_page_error.png")
                return

            await close_any_known_popup(page)

            # --- ETAPA 7: CLICAR NO BOTÃO GERAR ---
            print("Testando o botão 'Gerar' do relatório...")
            try:
                generate_button_selector = 'button[name="ButtonSave"][type="submit"]'
                print(f"🎯 Seletor do botão: {generate_button_selector}")
                print("Aguardando o botão 'Gerar' aparecer...")
                
                # Aguarda o botão estar visível
                await page.wait_for_selector(generate_button_selector, state='visible', timeout=30000)
                
                # Tira screenshot antes de clicar
                await page.screenshot(path="debug_before_generate_click.png", full_page=True)
                print("📸 Screenshot antes de clicar no botão 'Gerar' salvo: debug_before_generate_click.png")
                
                # Clica no botão Gerar
                await page.click(generate_button_selector)
                print("✅ Botão 'Gerar' clicado com sucesso!")
                
                # Aguarda um pouco para ver o resultado
                await page.wait_for_timeout(3000)
                
                # Tira screenshot após clicar
                await page.screenshot(path="debug_after_generate_click.png", full_page=True)
                print("📸 Screenshot após clicar no botão 'Gerar' salvo: debug_after_generate_click.png")
                
                # --- AGUARDAR GERAÇÃO DO RELATÓRIO ---
                print("⏳ Aguardando a geração do relatório ser concluída...")
                print("🔄 Isso pode levar alguns minutos...")
                
                # Aguarda um tempo maior para a geração
                await page.wait_for_timeout(10000)  # 10 segundos inicial
                
                # Aguarda a página estabilizar
                try:
                    await page.wait_for_load_state("load", timeout=60000)  # 1 minuto
                    print("✅ Página estabilizada após geração do relatório.")
                except TimeoutError:
                    print("⚠️ Timeout aguardando estabilização da página, mas continuando...")
                
                # Aguarda mais um tempo para garantir que o relatório foi gerado
                await page.wait_for_timeout(5000)  # 5 segundos adicionais
                
                # Tira screenshot após aguardar a geração
                await page.screenshot(path="debug_after_report_generation.png", full_page=True)
                print("📸 Screenshot após aguardar geração salvo: debug_after_report_generation.png")
                print("✅ Aguardou a geração do relatório ser concluída.")
                
            except TimeoutError:
                print(f"❌ Erro: Botão 'Gerar' não encontrado.")
                await page.screenshot(path="debug_generate_button_not_found.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_generate_button_not_found.png")
                return
            except Exception as e:
                print(f"❌ Erro inesperado ao clicar no botão 'Gerar': {e}")
                await page.screenshot(path="debug_generate_button_error.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_generate_button_error.png")
                return

            await close_any_known_popup(page)

            # --- ETAPA 8: AGUARDAR RELATÓRIO APARECER E BAIXAR ---
            print("\n" + "="*70)
            print("📍 ETAPA 8: AGUARDANDO E BAIXANDO O RELATÓRIO")
            print("="*70)
            print("⏳ Aguardando o relatório ser gerado...")
            print("🔄 Procurando pelo link 'Download'...")
            
            download_link_selector = 'a:has-text("Download")' 
            
            max_attempts = 20
            file_path = None
            
            for i in range(max_attempts):
                try:
                    print(f"\n🔄 Tentativa {i+1}/{max_attempts} - Procurando link 'Download'...")
                    
                    download_link = page.locator(download_link_selector).first
                    await download_link.wait_for(state='visible', timeout=10000)
                    
                    if await download_link.is_enabled():
                        print(f"✅ Link 'Download' encontrado e clicável após {i+1} tentativas!")
                        
                        await page.screenshot(path="debug_before_download.png", full_page=True)
                        print("📸 Screenshot antes do download: debug_before_download.png")
                        
                        async with page.expect_download() as download_info:
                            await download_link.click()
                            print("✅ Link 'Download' clicado!")
                        
                        download = await download_info.value
                        file_path = os.path.join(downloads_dir, download.suggested_filename)
                        await download.save_as(file_path)
                        print(f"✅ Relatório baixado com sucesso!")
                        print(f"📁 Arquivo: {file_path}")
                        break
                    else:
                        print(f"⏳ Link 'Download' visível, mas não habilitado. Aguardando 5 segundos...")
                        await page.wait_for_timeout(5000)
                        
                except TimeoutError:
                    print(f"⏳ Link 'Download' não visível na tentativa {i+1}/{max_attempts}. Aguardando 5 segundos...")
                    await page.wait_for_timeout(5000)
                    
                except Exception as e:
                    print(f"❌ Erro inesperado na tentativa {i+1}/{max_attempts}: {e}")
                    await page.wait_for_timeout(5000)
                    
            else:
                print(f"\n❌ ERRO: Link 'Download' não apareceu após {max_attempts} tentativas.")
                await page.screenshot(path="debug_download_link_not_available.png", full_page=True)
                print("📸 Screenshot de erro salvo: debug_download_link_not_available.png")
                return

            # --- ETAPA 9: PROCESSAR ARQUIVO E INSERIR NO SUPABASE ---
            print("\n" + "="*70)
            print("📍 ETAPA 9: PROCESSANDO ARQUIVO BAIXADO E INSERINDO NO BANCO")
            print("="*70)
            
            if file_path:
                print(f"📁 Arquivo baixado: {file_path}")
                
                # Verificar se arquivo existe
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"✅ Arquivo existe! Tamanho: {file_size} bytes")
                else:
                    print(f"❌ Arquivo não encontrado: {file_path}")
                    return
                
                # Ler o arquivo Excel
                print("\n📖 Lendo arquivo Excel...")
                df = read_excel_file(file_path)
                
                if df is not None and not df.empty:
                    print(f"✅ Arquivo lido com sucesso! {len(df)} linhas encontradas")
                    print(f"📊 Colunas: {df.columns.tolist()}")
                    
                    # Processar os dados
                    print("\n🔄 Processando dados...")
                    df_processed = processar_dados_publicacoes(df)
                    
                    if df_processed is not None and not df_processed.empty:
                        print(f"✅ Dados processados! {len(df_processed)} registros prontos")
                        print(f"📊 Colunas processadas: {df_processed.columns.tolist()}")
                        
                        # INSERIR NO BANCO
                        print("\n" + "="*70)
                        print("💾 INSERINDO DADOS NO SUPABASE")
                        print("="*70)
                        success = await inserir_dados_supabase(df_processed, "tb_publicacoes")
                        
                        # Inserir também no Azure SQL Database
                        if success:
                            print("\n[AZURE] Inserindo dados no Azure SQL Database...")
                            try:
                                azure_success = insert_publicacoes(df_processed, "publicacoes")
                                if azure_success:
                                    print("✅ Dados inseridos no Azure SQL Database com sucesso!")
                                else:
                                    print("❌ Falha ao inserir dados no Azure SQL Database.")
                            except Exception as e:
                                print(f"❌ Erro ao inserir no Azure SQL Database: {e}")
                        
                        if success:
                            print("\n" + "="*70)
                            print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
                            print("="*70)
                            print("📁 Arquivo baixado e processado")
                            print("💾 Dados inseridos na tabela tb_publicacoes")
                            print("📂 Arquivo mantido em: " + file_path)
                        else:
                            print("\n" + "="*70)
                            print("⚠️  PROCESSAMENTO CONCLUÍDO COM AVISOS")
                            print("="*70)
                            print("📁 Arquivo baixado e processado")
                            print("❌ Erro ao inserir dados no banco")
                            print("📂 Arquivo mantido em: " + file_path)
                    else:
                        print("❌ Erro no processamento dos dados.")
                else:
                    print("❌ Arquivo vazio ou erro ao ler o arquivo.")
            else:
                print("❌ Nenhum arquivo foi baixado.")

            print("\n" + "="*70)
            print("🎯 PROCESSO DE TESTE CONCLUÍDO")
            print("="*70)
            print(f"📍 URL atual: {page.url}")
            
            
            # Fechar navegador antes de sair do contexto do Playwright
            if browser:
                await browser.close()
                print("🔌 Navegador fechado.")
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO na função run(): {e}")
        import traceback
        traceback.print_exc()
        # Garantir que o navegador seja fechado mesmo em caso de erro
        if browser:
            try:
                await browser.close()
                print("🔌 Navegador fechado após erro.")
            except:
                pass
        raise  # Re-raise para ser capturado pelo handler principal

if __name__ == "__main__":
    import sys
    import datetime
    
    # Criar arquivo de log para capturar todos os erros
    log_file = f"rpa_publicacoes_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    class TeeOutput:
        """Classe para escrever simultaneamente no console e no arquivo"""
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    # Redirecionar stdout e stderr para arquivo e console
    log_f = open(log_file, 'w', encoding='utf-8')
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = TeeOutput(sys.stdout, log_f)
    sys.stderr = TeeOutput(sys.stderr, log_f)
    
    try:
        print("="*70)
        print("🚀 INICIANDO RPA DE PUBLICAÇÕES")
        print(f"📝 Log sendo salvo em: {log_file}")
        print("="*70)
        asyncio.run(run())
        print("\n" + "="*70)
        print("✅ RPA FINALIZADO")
        print("="*70)
    except KeyboardInterrupt:
        print("\n⚠️  RPA interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERRO FATAL no RPA: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70)
        print("❌ RPA FINALIZADO COM ERRO")
        print(f"📝 Erro completo salvo em: {log_file}")
        print("="*70)
    finally:
        # Restaurar stdout e stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_f.close()
        print(f"\n📝 Log completo salvo em: {log_file}")

