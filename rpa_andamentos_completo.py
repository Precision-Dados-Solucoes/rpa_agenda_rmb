#!/usr/bin/env python3
"""
RPA Completo para Andamentos - Download + Processamento + UPSERT
Integra download do relatório com processamento e inserção no Supabase
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis de ambiente
load_dotenv('config.env')

# --- Configuração da pasta de downloads ---
downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
print(f"A pasta de downloads sera: {os.path.abspath(downloads_dir)}")

# --- Nome do arquivo de andamentos esperado ---
expected_filename = "z-rpa_andamentos_agenda_rmb_queeue"
print(f"Nome do arquivo esperado: {expected_filename}")

async def close_any_known_popup(page):
    """Tenta fechar popups modais ou overlays usando seletores comuns para botões de fechar."""
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

def extract_date_from_datetime(datetime_str):
    """Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss e converte para aaaa-mm-dd"""
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.strftime('%Y-%m-%d')
    except:
        return None

async def process_excel_file(file_path):
    """Processa o arquivo Excel baixado com todos os tratamentos necessários."""
    print("Iniciando processamento do arquivo Excel...")
    
    try:
        df = pd.read_excel(file_path)
        print(f"Arquivo lido com sucesso. Linhas: {len(df)}")
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None
    
    try:
        # Criar DataFrame processado com as colunas do Supabase
        df_processed = pd.DataFrame()
        
        # Mapeamento direto (sem tratamento)
        direct_mappings = {
            'id_agenda_legalone': 'id_agenda_legalone',
            'id_andamento_legalone': 'id_andamento_legalone',
            'tipo_andamento': 'tipo_andamento',
            'subtipo_andamento': 'subtipo_andamento',
            'descricao_andamento': 'descricao_andamento'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"Coluna '{excel_col}' -> '{supabase_col}'")
            else:
                print(f"Coluna '{excel_col}' nao encontrada no arquivo")
                df_processed[supabase_col] = None
        
        # Tratamento especial para campo 'cadastro_andamento'
        print("Processando campo 'cadastro_andamento'...")
        if 'cadastro_andamento' in df.columns:
            df_processed['cadastro_andamento'] = df['cadastro_andamento'].apply(extract_date_from_datetime)
            print("Campo 'cadastro_andamento' processado (dd/mm/aaaa hh:mm:ss -> aaaa/mm/dd)")
        else:
            print("Coluna 'cadastro_andamento' nao encontrada no arquivo")
            df_processed['cadastro_andamento'] = None
        
        # Limpar dados e converter tipos
        print("Limpando dados e convertendo tipos...")
        
        # Converter campos int8
        int8_columns = ['id_agenda_legalone', 'id_andamento_legalone']
        for col in int8_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').astype('Int64')
                print(f"Campo '{col}' convertido para int8")
        
        # Converter campos text
        text_columns = ['tipo_andamento', 'subtipo_andamento', 'descricao_andamento']
        for col in text_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].astype(str)
                print(f"Campo '{col}' convertido para text")
        
        # Converter campo date
        if 'cadastro_andamento' in df_processed.columns:
            valid_dates = df_processed['cadastro_andamento'].notna().sum()
            print(f"Campo 'cadastro_andamento' processado: {valid_dates} datas validas")
        
        print(f"Processamento concluido. Linhas processadas: {len(df_processed)}")
        print("Colunas finais:")
        print(df_processed.columns.tolist())
        
        return df_processed
        
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        return None

# Variáveis globais para conexão
conn = None

async def connect_to_database():
    """Conecta ao banco de dados Supabase"""
    global conn
    
    # Credenciais do Supabase
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "PDS2025@@")

    print(f"Conectando ao Supabase: {host}:{port}/{database}")
    print(f"Usuario: {user}")
    
    try:
        conn = await asyncpg.connect(
            user=user, 
            password=password,
            host=host, 
            port=int(port), 
            database=database,
            command_timeout=30,
            statement_cache_size=0,
            server_settings={
                'application_name': 'rpa_andamentos_rmb',
                'tcp_keepalives_idle': '60',
                'tcp_keepalives_interval': '10',
                'tcp_keepalives_count': '3',
                'statement_timeout': '60000',
                'idle_in_transaction_session_timeout': '60000'
            }
        )
        print("Conexao com o Supabase estabelecida com sucesso!")
        
        # Teste de conectividade
        version = await conn.fetchval("SELECT version()")
        print(f"Versao do PostgreSQL: {version[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"Erro na conexao: {e}")
        return False

async def process_dataframe_with_upsert(df, table_name):
    """Processa DataFrame com sistema UPSERT"""
    global conn
    
    try:
        print(f"Processando {len(df)} registros com UPSERT...")
        
        # Verificar se a tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            print(f"ERRO: Tabela '{table_name}' nao existe no Supabase!")
            return False
        
        print(f"Tabela '{table_name}' encontrada!")
        
        # Contar registros existentes
        count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        print(f"Registros existentes na tabela: {count_before}")
        
        # Processar cada registro com UPSERT
        updated_count = 0
        inserted_count = 0
        
        for index, row in df.iterrows():
            try:
                # Verificar se o registro ja existe
                existing_record = await conn.fetchrow("""
                    SELECT id_andamento_legalone FROM {} WHERE id_andamento_legalone = $1
                """.format(table_name), row['id_andamento_legalone'])
                
                if existing_record:
                    # ATUALIZAR registro existente
                    await conn.execute("""
                        UPDATE {} SET 
                            id_agenda_legalone = $1,
                            tipo_andamento = $2,
                            subtipo_andamento = $3,
                            descricao_andamento = $4,
                            cadastro_andamento = $5
                        WHERE id_andamento_legalone = $6
                    """.format(table_name), 
                        row['id_agenda_legalone'],
                        row['tipo_andamento'],
                        row['subtipo_andamento'],
                        row['descricao_andamento'],
                        row['cadastro_andamento'],
                        row['id_andamento_legalone']
                    )
                    updated_count += 1
                    print(f"Registro atualizado: id_andamento_legalone = {row['id_andamento_legalone']}")
                else:
                    # INSERIR novo registro
                    await conn.execute("""
                        INSERT INTO {} (
                            id_agenda_legalone, 
                            id_andamento_legalone, 
                            tipo_andamento, 
                            subtipo_andamento, 
                            descricao_andamento, 
                            cadastro_andamento
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """.format(table_name),
                        row['id_agenda_legalone'],
                        row['id_andamento_legalone'],
                        row['tipo_andamento'],
                        row['subtipo_andamento'],
                        row['descricao_andamento'],
                        row['cadastro_andamento']
                    )
                    inserted_count += 1
                    print(f"Registro inserido: id_andamento_legalone = {row['id_andamento_legalone']}")
                    
            except Exception as e:
                print(f"Erro ao processar registro {index}: {e}")
                continue
        
        # Verificar resultado final
        count_after = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        
        print(f"\nUPSERT CONCLUIDO:")
        print(f"Registros atualizados: {updated_count}")
        print(f"Registros inseridos: {inserted_count}")
        print(f"Total processados: {updated_count + inserted_count}")
        print(f"Registros na tabela: {count_before} -> {count_after}")
        
        return True
        
    except Exception as e:
        print(f"Erro durante UPSERT: {e}")
        return False

async def close_connection():
    """Fecha a conexão com o banco"""
    global conn
    if conn:
        await conn.close()
        print("Conexao fechada com sucesso!")

async def run():
    """Executa o RPA completo: download + processamento + UPSERT"""
    async with async_playwright() as p:
        # Configuração automática do modo headless baseada no ambiente
        # Detecta se está em ambiente sem interface gráfica (GitHub Actions, etc.)
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        
        # Se estiver em ambiente CI/CD (GitHub Actions), força headless
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            headless_mode = True
        
        print(f"Executando em modo {'headless' if headless_mode else 'com interface grafica'}")
        
        # Configurações otimizadas para CI/CD
        browser_args = []
        if headless_mode:
            browser_args.extend([
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ])
        
        browser = await p.chromium.launch(
            headless=headless_mode,
            args=browser_args
        )
        
        chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" 
        context = await browser.new_context(user_agent=chrome_user_agent)
        
        page = await context.new_page()

        # --- CREDENCIAIS DE LOGIN NO SISTEMA NOVAJUS ---
        USERNAME = os.getenv("NOVAJUS_USERNAME", "cleiton.sanches@precisionsolucoes.com")
        PASSWORD = os.getenv("NOVAJUS_PASSWORD", "PDS2025@")

        # --- ETAPA 1: NAVEGAR PARA A PÁGINA DE LOGIN ---
        novajus_login_url = "https://login.novajus.com.br/conta/login" 
        print(f"Navegando para {novajus_login_url}...")
        
        try:
            # Timeout mais longo para CI/CD
            timeout_duration = 120000 if headless_mode else 60000
            await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=timeout_duration) 
            print(f"DEBUG: URL atual após page.goto(): {page.url}")
            await page.screenshot(path="debug_andamentos_initial_page.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_andamentos_initial_page.png' tirada após page.goto().")
        except TimeoutError:
            print(f"Erro FATAL: page.goto() para {novajus_login_url} excedeu o tempo limite.")
            await page.screenshot(path="debug_andamentos_initial_page_timeout.png", full_page=True)
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para a página de login: {e}")
            await page.screenshot(path="debug_andamentos_initial_page_error.png", full_page=True)
            await browser.close()
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
                await page.screenshot(path="debug_andamentos_after_onepass_click.png", full_page=True)
            else:
                print("Botão OnePass não visível. Prosseguindo.")
        except TimeoutError:
            print("Botão OnePass não encontrado no tempo esperado. Assumindo que já está na tela principal.")
        except Exception as e:
            print(f"Erro ao lidar com o botão OnePass: {e}")

        # --- ETAPA 2: INSERIR E-MAIL ---
        print("Aguardando o campo de e-mail '#Username' aparecer e ficar visível...")
        try:
            await page.wait_for_selector('#Username', state='visible', timeout=30000)
            print(f"Preenchendo e-mail: {USERNAME}...")
            await page.fill('#Username', USERNAME)
            
            await page.keyboard.press('Tab') 
            print("Pressionado TAB após preencher o e-mail. Aguardando a tela de senha mudar...")
            
            await page.wait_for_selector('#password', state='visible', timeout=30000) 
            print("Nova tela de senha com ID '#password' detectada.")
            await page.screenshot(path="debug_andamentos_after_username_fill.png", full_page=True)
            
        except TimeoutError:
            print("Erro FATAL: Campo de e-mail '#Username' ou transição para senha não ocorreu no tempo esperado.")
            await page.screenshot(path="debug_andamentos_username_or_transition_error.png", full_page=True)
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher e-mail e aguardar transição: {e}")
            await page.screenshot(path="debug_andamentos_username_fill_error.png", full_page=True)
            await browser.close()
            return

        # --- ETAPA 3: INSERIR SENHA E CLICAR NO BOTÃO FINAL DE LOGIN ---
        print("Preenchendo senha no campo '#password'...")
        try:
            await page.fill('#password', PASSWORD)
            print("Senha preenchida.")

            login_button_selector = 'button._button-login-password'
            print(f"Clicando no botão 'Entrar' final '{login_button_selector}'...")
            await page.wait_for_selector(login_button_selector, state='visible', timeout=30000)
            await page.click(login_button_selector)
            print("Botão 'Entrar' final clicado.")

            print("Aguardando o carregamento completo da página após o login (networkidle)...")
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            await page.screenshot(path="debug_andamentos_after_final_login_click.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_andamentos_after_final_login_click.png' tirada após o login.")
            print(f"DEBUG: URL atual após login: {page.url}")

        except TimeoutError:
            print("Erro FATAL: Campo de senha '#password' ou botão de login final não apareceu/clicável no tempo esperado.")
            await page.screenshot(path="debug_andamentos_password_field_or_final_button_missing.png", full_page=True)
            print("Erro capturado em screenshot. Fechando navegador.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher senha ou clicar no botão final: {e}")
            await page.screenshot(path="debug_andamentos_password_fill_or_final_click_error.png", full_page=True)
            print("Erro capturado em screenshot. Fechando navegador.")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 4: SELEÇÃO DA NOVA LICENÇA ---
        print("Aguardando página de seleção de licença carregar...")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="debug_andamentos_license_selection_page.png", full_page=True)
        print("Screenshot da página de seleção de licença salvo: debug_andamentos_license_selection_page.png")

        # --- SELEÇÃO DA LICENÇA CORRETA USANDO CURRENT-VALUE ---
        print("Selecionando a licença usando current-value...")
        try:
            license_specific_value = "64ee2867d98cf01183cb12fc83a1b95d"
            license_selector = f'saf-radio[current-value="{license_specific_value}"] >> input[part="control"]'
            
            print(f"Valor da licença: {license_specific_value}")
            print(f"Seletor: {license_selector}")
            print("Aguardando e clicando na licença específica...")
            
            await page.wait_for_selector(license_selector, state='visible', timeout=30000)
            await page.click(license_selector)
            print("Licença 'robertomatos - cleiton.sanches' selecionada com sucesso!")

        except TimeoutError:
            print(f"Erro: Licença com current-value '{license_specific_value}' não encontrada.")
            await page.screenshot(path="debug_andamentos_license_current_value_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_license_current_value_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao selecionar a licença: {e}")
            await page.screenshot(path="debug_andamentos_license_current_value_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_license_current_value_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # Clicar no botão 'Continuar' após selecionar a licença
        print("Clicando no botão 'Continuar' após selecionar a licença...")
        try:
            continue_button_selector = 'saf-button.PersonaSelectionPage-button[type="submit"]' 
            await page.wait_for_selector(continue_button_selector, state='visible', timeout=30000)
            await page.click(continue_button_selector)
            print("Botão 'Continuar' clicado com sucesso!")

        except TimeoutError:
            print(f"Erro: Botão 'Continuar' não encontrado.")
            await page.screenshot(path="debug_andamentos_continue_button_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_continue_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao clicar no botão continuar: {e}")
            await page.screenshot(path="debug_andamentos_continue_button_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_continue_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 5: ESPERA DA PÁGINA PÓS-LOGIN COMPLETO ---
        print("Aguardando a página inicial do sistema carregar...")
        await page.wait_for_load_state("networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        print(f"URL atual após login completo: {page.url}")
        await page.screenshot(path="debug_andamentos_post_login_page.png", full_page=True)
        print("Screenshot da página pós-login salvo: debug_andamentos_post_login_page.png")

        await close_any_known_popup(page)

        # --- ETAPA 6: NAVEGAR PARA O RELATÓRIO DE ANDAMENTOS ---
        report_url = "https://robertomatos.novajus.com.br/agenda/GenericReport/?id=672"
        print(f"Navegando para o relatório de andamentos: {report_url}...")
        try:
            await page.goto(report_url, wait_until="domcontentloaded", timeout=60000)
            print(f"URL atual após navegar para o relatório: {page.url}")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="debug_andamentos_report_page_loaded.png", full_page=True)
            print("Screenshot da página do relatório salvo: debug_andamentos_report_page_loaded.png")
        except TimeoutError:
            print(f"Erro: Página do relatório não carregou no tempo esperado.")
            await page.screenshot(path="debug_andamentos_report_page_load_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_report_page_load_error.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para o relatório: {e}")
            await page.screenshot(path="debug_andamentos_report_page_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_report_page_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 7: CLICAR NO BOTÃO GERAR ---
        print("Testando o botão 'Gerar' do relatório de andamentos...")
        try:
            generate_button_selector = 'button[name="ButtonSave"][type="submit"]'
            print(f"Seletor do botão: {generate_button_selector}")
            print("Aguardando o botão 'Gerar' aparecer...")
            
            await page.wait_for_selector(generate_button_selector, state='visible', timeout=30000)
            
            await page.screenshot(path="debug_andamentos_before_generate_click.png", full_page=True)
            print("Screenshot antes de clicar no botão 'Gerar' salvo: debug_andamentos_before_generate_click.png")
            
            await page.click(generate_button_selector)
            print("Botão 'Gerar' clicado com sucesso!")
            
            await page.wait_for_timeout(3000)
            
            await page.screenshot(path="debug_andamentos_after_generate_click.png", full_page=True)
            print("Screenshot após clicar no botão 'Gerar' salvo: debug_andamentos_after_generate_click.png")
            
            # --- AGUARDAR GERAÇÃO DO RELATÓRIO ---
            print("Aguardando a geração do relatório ser concluída...")
            print("Isso pode levar alguns minutos...")
            
            await page.wait_for_timeout(10000)
            
            try:
                await page.wait_for_load_state("networkidle", timeout=120000)
                print("Página estabilizada após geração do relatório.")
            except TimeoutError:
                print("Timeout aguardando estabilização da página, mas continuando...")
            
            await page.wait_for_timeout(5000)
            
            await page.screenshot(path="debug_andamentos_after_report_generation.png", full_page=True)
            print("Screenshot após aguardar geração salvo: debug_andamentos_after_report_generation.png")
            print("Aguardou a geração do relatório ser concluída.")
            
        except TimeoutError:
            print(f"Erro: Botão 'Gerar' não encontrado.")
            await page.screenshot(path="debug_andamentos_generate_button_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_generate_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao clicar no botão 'Gerar': {e}")
            await page.screenshot(path="debug_andamentos_generate_button_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_generate_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 8: AGUARDAR RELATÓRIO APARECER E BAIXAR ---
        print("Aguardando o relatório ser gerado e aparecer na página atual...")
        print("Procurando pelo link 'Download' do relatório...")
        
        download_link_selector = 'a:has-text("Download")' 
        
        max_attempts = 20
        file_path = None
        
        for i in range(max_attempts):
            try:
                print(f"Tentativa {i+1}/{max_attempts} - Procurando link 'Download'...")
                
                download_link = page.locator(download_link_selector).first
                await download_link.wait_for(state='visible', timeout=10000)
                
                if await download_link.is_enabled():
                    print(f"Link 'Download' encontrado e clicável após {i+1} tentativas!")
                    
                    await page.screenshot(path="debug_andamentos_before_download.png", full_page=True)
                    print("Screenshot antes do download salvo: debug_andamentos_before_download.png")
                    
                    async with page.expect_download() as download_info:
                        await download_link.click()
                        print("Link 'Download' clicado.")
                    
                    download = await download_info.value
                    file_path = os.path.join(downloads_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    print(f"Relatório de andamentos baixado com sucesso: {file_path}")
                    
                    # Verificar se o nome do arquivo contém o padrão esperado
                    if expected_filename in download.suggested_filename:
                        print(f"Nome do arquivo correto: contém '{expected_filename}'")
                    else:
                        print(f"Nome do arquivo diferente do esperado:")
                        print(f"   Esperado: {expected_filename}")
                        print(f"   Obtido: {download.suggested_filename}")
                    
                    break
                else:
                    print(f"Link 'Download' visível, mas não habilitado. Aguardando...")
                    await page.wait_for_timeout(5000)
                    
            except TimeoutError:
                print(f"Link 'Download' não visível na tentativa {i+1}/{max_attempts}. Aguardando...")
                await page.wait_for_timeout(5000)
                
            except Exception as e:
                print(f"Erro inesperado na tentativa {i+1}/{max_attempts}: {e}")
                await page.wait_for_timeout(5000)
                
        else:
            print(f"Erro: Link 'Download' não apareceu após {max_attempts} tentativas.")
            await page.screenshot(path="debug_andamentos_download_link_not_available.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_download_link_not_available.png")
            await browser.close()
            return

        # --- ETAPA 9: PROCESSAR ARQUIVO E INSERIR NO SUPABASE ---
        print("\n" + "="*70)
        print("PROCESSANDO ARQUIVO BAIXADO E INSERINDO NO SUPABASE")
        print("="*70)
        
        if file_path:
            print(f"Arquivo baixado: {file_path}")
            
            # Processar o arquivo Excel
            df_processed = await process_excel_file(file_path)
            
            if df_processed is not None and not df_processed.empty:
                # Conectar ao banco e fazer UPSERT
                try:
                    if not await connect_to_database():
                        print("Erro ao conectar ao banco de dados")
                        await browser.close()
                        return
                    
                    # Processar com UPSERT
                    success = await process_dataframe_with_upsert(df_processed, "andamento_base")
                    
                    if success:
                        print("Dados inseridos/atualizados no Supabase com sucesso!")
                    else:
                        print("Falha ao inserir/atualizar dados no Supabase.")
                        
                except Exception as e:
                    print(f"Erro durante processamento: {e}")
                finally:
                    await close_connection()
            else:
                print("Arquivo vazio ou erro no processamento.")
        else:
            print("Nenhum arquivo foi baixado.")

        # --- FINALIZAÇÃO ---
        print("\n" + "="*70)
        print("RPA COMPLETO FINALIZADO")
        print("="*70)
        print("Processo completo realizado com sucesso!")
        print("Login, seleção de licença, geração, download e processamento do relatório")
        print(f"URL atual: {page.url}")
        if file_path:
            print(f"Arquivo baixado: {file_path}")
        
        # Fechar navegador imediatamente
        await browser.close()
        print("Navegador fechado com sucesso!")
        return

# --- Execução principal do script ---
if __name__ == "__main__":
    print("RPA ANDAMENTOS RMB - VERSÃO COMPLETA")
    print("Este script automatiza a extração, processamento e inserção de andamentos")
    print("Otimizado para execução automática (GitHub Actions)")
    print("Modo: Headless automático baseado no ambiente")
    print("")
    
    asyncio.run(run())
