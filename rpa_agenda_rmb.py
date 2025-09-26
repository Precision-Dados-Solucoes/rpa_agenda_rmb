import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import pandas as pd
import asyncpg
from dotenv import load_dotenv

# --- INSTALAÇÃO DE BIBLIOTECAS (rode estes comandos no seu terminal se ainda não o fez): ---
# pip install pandas
# pip install asyncpg
# pip install python-dotenv
# pip install openpyxl
# -----------------------------------------------------------------------------------------

# Carrega as variáveis de ambiente do arquivo config.env
# Certifique-se de ter um arquivo config.env no mesmo diretório do seu script com as credenciais:
# SUPABASE_HOST=db.dhfmqumwizrwdbjnbcua.supabase.co
# SUPABASE_PORT=5432
# SUPABASE_DATABASE=postgres
# SUPABASE_USER=postgres
# SUPABASE_PASSWORD=PDS2025@@
load_dotenv('config.env')

# Configuração automática do modo headless baseada no ambiente

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
        '[aria-label="Close"]',          # Botão genérico de fechar (com label ARIA)
        'button:has-text("Fechar")',     # Botão com texto "Fechar"
        'button:has-text("OK")',         # Às vezes "OK" fechar um aviso
        'button.close',                  # Classe comum para botões de fechar
        '.modal-footer button:has-text("Fechar")', # Botão "Fechar" no rodapé de um modal
        '.modal-header button.close',    # Botão "Fechar" no cabeçalho de um modal
        '.popup-close',                  # Classe específica para fechar popups
        '#close-button',                 # ID comum para um botão de fechar
        '[role="dialog"] button:has-text("Fechar")' # Botão fechar dentro de um elemento com role="dialog"
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
    Lê um arquivo Excel (ou CSV) e retorna um DataFrame do pandas.
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
        print("Primeiras 5 linhas do DataFrame:")
        print(df.head())
        print(f"Colunas do DataFrame: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None

async def process_excel_file(file_path):
    """
    Processa o arquivo Excel baixado com todos os tratamentos necessários.
    """
    print("🔄 Iniciando processamento do arquivo Excel...")
    
    # 1. Ler o arquivo
    df = read_excel_file(file_path)
    if df is None or df.empty:
        print("❌ Erro: Não foi possível ler o arquivo ou arquivo vazio.")
        return None
    
    print(f"📊 Arquivo lido com sucesso. Linhas: {len(df)}")
    
    try:
        # 2. Criar DataFrame processado com as colunas do Supabase
        df_processed = pd.DataFrame()
        
        # Mapeamento direto (sem tratamento)
        direct_mappings = {
            'id_legalone': 'id_legalone',
            'compromisso_tarefa': 'compromisso_tarefa', 
            'tipo': 'tipo',
            'subtipo': 'subtipo',
            'etiqueta': 'etiqueta',
            'pasta_proc': 'Pasta_proc',
            'numero_cnj': 'numero_cnj',
            'executante': 'executante',
            'executante_sim': 'executante_sim',
            'descricao': 'descricao',
            'status': 'status'
        }
        
        # Copiar colunas diretas
        for supabase_col, excel_col in direct_mappings.items():
            if excel_col in df.columns:
                df_processed[supabase_col] = df[excel_col]
                print(f"✅ Coluna '{excel_col}' → '{supabase_col}'")
            else:
                print(f"⚠️ Coluna '{excel_col}' não encontrada no arquivo")
                df_processed[supabase_col] = None
        
        # 3. Tratamento de campos de data/hora
        print("🔄 Processando campos de data/hora...")
        
        # Tratar campo 'inicio' (dd/mm/aaaa hh:mm:ss)
        if 'inicio' in df.columns:
            df_processed['inicio_data'] = df['inicio'].apply(extract_date_from_datetime)
            df_processed['inicio_hora'] = df['inicio'].apply(extract_time_from_datetime)
            print("✅ Campo 'inicio' processado → 'inicio_data' e 'inicio_hora'")
        
        # Tratar campo 'conclusao_prevista' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_prevista' in df.columns:
            df_processed['conclusao_prevista_data'] = df['conclusao_prevista'].apply(extract_date_from_datetime)
            df_processed['conclusao_prevista_hora'] = df['conclusao_prevista'].apply(extract_time_from_datetime)
            print("✅ Campo 'conclusao_prevista' processado → 'conclusao_prevista_data' e 'conclusao_prevista_hora'")
        
        # Tratar campo 'conclusao_efetiva' (dd/mm/aaaa hh:mm:ss)
        if 'conclusao_efetiva' in df.columns:
            df_processed['conclusao_efetiva_data'] = df['conclusao_efetiva'].apply(extract_date_from_datetime)
            print("✅ Campo 'conclusao_efetiva' processado → 'conclusao_efetiva_data'")
        
        # 4. Gerar campo 'link' concatenado
        if 'id_legalone' in df_processed.columns:
            df_processed['link'] = df_processed['id_legalone'].apply(generate_link)
            print("✅ Campo 'link' gerado com sucesso")
        
        # 5. Filtrar apenas linhas onde executante_sim = "Sim"
        print("🔄 Filtrando linhas onde executante_sim = 'Sim'...")
        if 'executante_sim' in df_processed.columns:
            linhas_antes = len(df_processed)
            df_processed = df_processed[df_processed['executante_sim'] == 'Sim']
            linhas_depois = len(df_processed)
            print(f"✅ Filtro aplicado: {linhas_antes} → {linhas_depois} linhas (removidas {linhas_antes - linhas_depois} linhas com 'Não')")
        else:
            print("⚠️ Coluna 'executante_sim' não encontrada, pulando filtro")
        
        # 6. Limpar dados nulos e converter tipos
        print("🔄 Limpando dados e convertendo tipos...")
        
        # Converter id_legalone para int8
        if 'id_legalone' in df_processed.columns:
            df_processed['id_legalone'] = pd.to_numeric(df_processed['id_legalone'], errors='coerce').astype('Int64')
        
        # Converter campos numéricos para string (text no Supabase)
        text_columns = ['pasta_proc', 'numero_cnj', 'executante', 'executante_sim', 'descricao', 'link', 'status']
        for col in text_columns:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].astype(str)
                print(f"✅ Campo '{col}' convertido para string")
        
        # Converter campos de data
        date_columns = ['inicio_data', 'conclusao_prevista_data', 'conclusao_efetiva_data']
        for col in date_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.date
        
        # Converter campos de hora
        time_columns = ['inicio_hora', 'conclusao_prevista_hora']
        for col in time_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.time
        
        print(f"✅ Processamento concluído. Linhas processadas: {len(df_processed)}")
        print("📊 Colunas finais:")
        print(df_processed.columns.tolist())
        
        return df_processed
        
    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
        return None

def extract_date_from_datetime(datetime_str):
    """
    Extrai a data de uma string no formato dd/mm/aaaa hh:mm:ss
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Converte string para datetime
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.date()
    except:
        return None

def extract_time_from_datetime(datetime_str):
    """
    Extrai a hora de uma string no formato dd/mm/aaaa hh:mm:ss
    """
    if pd.isna(datetime_str) or datetime_str == '':
        return None
    
    try:
        # Converte string para datetime
        dt = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if pd.isna(dt):
            return None
        return dt.time()
    except:
        return None

def generate_link(id_legalone):
    """
    Gera o link concatenado baseado no id_legalone
    """
    if pd.isna(id_legalone):
        return None
    
    base_url = "https://robertomatos.novajus.com.br/agenda/compromissos/DetailsCompromissoTarefa/"
    params = "?hasNavigation=True&currentPage=1&returnUrl=%2Fagenda%2FCompromissoTarefa%2FSearch"
    
    return f"{base_url}{id_legalone}{params}"

async def insert_data_to_supabase(df, table_name):
    """
    Insere os dados de um DataFrame do pandas em uma tabela do Supabase.
    """
    # Credenciais do Supabase com fallback (como no Novajus)
    host = os.getenv("SUPABASE_HOST", "db.dhfmqumwizrwdbjnbcua.supabase.co")
    port = os.getenv("SUPABASE_PORT", "5432")
    database = os.getenv("SUPABASE_DATABASE", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD", "**PDS2025@@")

    print(f"🔗 Conectando ao Supabase: {host}:{port}/{database}")
    print(f"👤 Usuário: {user}")
    print(f"🔐 Senha: {'*' * len(password)}")

    # Configurações de retry
    max_retries = 3
    retry_delay = 5  # segundos
    
    for attempt in range(max_retries):
        conn = None
        try:
            print(f"🔄 Tentativa {attempt + 1}/{max_retries} - Conectando ao Supabase...")
            
            # Timeout de conexão mais longo para GitHub Actions
            conn = await asyncpg.connect(
                user=user, 
                password=password,
                host=host, 
                port=int(port), 
                database=database,
                command_timeout=60,  # 60 segundos para comandos
                server_settings={
                    'application_name': 'rpa_agenda_rmb',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3'
                }
            )
            print("✅ Conexão com o Supabase estabelecida com sucesso!")
            break
            
        except Exception as e:
            print(f"❌ Erro na tentativa {attempt + 1}: {e}")
            if conn:
                await conn.close()
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay} segundos antes da próxima tentativa...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Falha após {max_retries} tentativas. Pulando inserção no Supabase.")
                return False

    # Se chegou aqui, a conexão foi estabelecida com sucesso
    try:
        columns_df = df.columns.tolist()
        
        # Prepara a query SQL de INSERT
        # IMPORTANTE: Os nomes das colunas aqui (columns_sql) devem ser EXATAMENTE
        # os nomes das colunas na sua tabela do Supabase.
        # Eles vêm diretamente dos nomes das colunas do DataFrame, que você já
        # renomeou anteriormente.
        columns_sql = ", ".join(f'"{col}"' for col in columns_df) 
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns_df)))
        insert_query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"

        print(f"📊 Preparando para inserir {len(df)} linhas na tabela '{table_name}'...")
        async with conn.transaction():
            for index, row in df.iterrows():
                values = tuple(row.values)
                # Verifica se há valores NaN e converte para None (NULL no DB)
                # asyncpg não aceita np.nan, apenas None
                cleaned_values = tuple(None if pd.isna(v) else v for v in values)
                await conn.execute(insert_query, *cleaned_values)
            print(f"✅ Todas as {len(df)} linhas inseridas com sucesso na tabela '{table_name}'.")
        
        return True

    except Exception as e:
        print(f"❌ Erro ao inserir dados no Supabase: {e}")
        return False
    finally:
        if conn:
            await conn.close()
            print("🔌 Conexão com o Supabase fechada.")

async def run():
    async with async_playwright() as p:
        # Configuração automática do modo headless
        # Detecta se está em ambiente sem interface gráfica (GitHub Actions, etc.)
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        
        # Se estiver em ambiente CI/CD (GitHub Actions), força headless
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            headless_mode = True
            
        print(f"Executando em modo {'headless' if headless_mode else 'com interface gráfica'}")
        browser = await p.chromium.launch(headless=headless_mode)
        
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
            await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=60000) 
            print(f"DEBUG: URL atual após page.goto(): {page.url}")
            await page.screenshot(path="debug_initial_page.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_initial_page.png' tirada após page.goto().")
        except TimeoutError:
            print(f"Erro FATAL: page.goto() para {novajus_login_url} excedeu o tempo limite. Verifique sua conexão ou a URL.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para a página de login: {e}")
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
                await page.wait_for_timeout(1000) # Pequena pausa
                print("Clicou em OnePass. Aguardando a tela de login principal.")
                await page.screenshot(path="debug_after_onepass_click.png", full_page=True)
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
            await page.screenshot(path="debug_after_username_fill.png", full_page=True)
            
        except TimeoutError:
            print("Erro FATAL: Campo de e-mail '#Username' ou transição para senha não ocorreu no tempo esperado.")
            await page.screenshot(path="debug_username_or_transition_error.png", full_page=True)
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher e-mail e aguardar transição: {e}")
            await page.screenshot(path="debug_username_fill_error.png", full_page=True)
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
            
            await page.screenshot(path="debug_after_final_login_click.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_after_final_login_click.png' tirada após o login.")
            print(f"DEBUG: URL atual após login: {page.url}")

        except TimeoutError:
            print("Erro FATAL: Campo de senha '#password' ou botão de login final não apareceu/clicável no tempo esperado OU a página após o login não carregou totalmente.")
            await page.screenshot(path="debug_password_field_or_final_button_missing.png", full_page=True)
            print("Navegador mantido aberto para inspeção. Verifique a URL e o conteúdo da página.")
            if not headless_mode:
                await asyncio.Event().wait()
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher senha ou clicar no botão final: {e}")
            await page.screenshot(path="debug_password_fill_or_final_click_error.png", full_page=True)
            print("Navegador mantido aberto para inspeção. Verifique a URL e o conteúdo da página.")
            if not headless_mode:
                await asyncio.Event().wait()
            await browser.close()
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
            license_specific_value = "64ee2867d98cf01183cb12fc83a1b95d"
            
            # Seletor para o saf-radio com o current-value específico
            license_selector = f'saf-radio[current-value="{license_specific_value}"] >> input[part="control"]'
            
            print(f"🎯 Valor da licença: {license_specific_value}")
            print(f"🎯 Seletor: {license_selector}")
            print("Aguardando e clicando na licença específica...")
            
            # Aguarda o elemento estar visível
            await page.wait_for_selector(license_selector, state='visible', timeout=30000)
            
            # Clica na licença específica
            await page.click(license_selector)
            print("✅ Licença 'robertomatos - cleiton.sanches' selecionada com sucesso!")

        except TimeoutError:
            print(f"❌ Erro: Licença com current-value '{license_specific_value}' não encontrada.")
            await page.screenshot(path="debug_license_current_value_not_found.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_license_current_value_not_found.png")
            print("🔍 Verifique se a licença está visível na página.")
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao selecionar a licença: {e}")
            await page.screenshot(path="debug_license_current_value_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_license_current_value_error.png")
            await browser.close()
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
            print("📸 Screenshot de erro salvo: debug_continue_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao clicar no botão continuar: {e}")
            await page.screenshot(path="debug_continue_button_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_continue_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 5: ESPERA DA PÁGINA PÓS-LOGIN COMPLETO ---
        print("Aguardando a página inicial do sistema carregar...")
        await page.wait_for_load_state("networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        print(f"📍 URL atual após login completo: {page.url}")
        await page.screenshot(path="debug_post_login_page.png", full_page=True)
        print("📸 Screenshot da página pós-login salvo: debug_post_login_page.png")

        await close_any_known_popup(page)

        # --- ETAPA 6: NAVEGAR PARA O RELATÓRIO ---
        report_url = "https://robertomatos.novajus.com.br/agenda/GenericReport/?id=671"
        print(f"Navegando para o relatório: {report_url}...")
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
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao navegar para o relatório: {e}")
            await page.screenshot(path="debug_report_page_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_report_page_error.png")
            await browser.close()
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
            
            # Aguarda a página estabilizar (networkidle)
            try:
                await page.wait_for_load_state("networkidle", timeout=120000)  # 2 minutos
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
            await browser.close()
            return
        except Exception as e:
            print(f"❌ Erro inesperado ao clicar no botão 'Gerar': {e}")
            await page.screenshot(path="debug_generate_button_error.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_generate_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 8: AGUARDAR RELATÓRIO APARECER E BAIXAR ---
        print("⏳ Aguardando o relatório ser gerado e aparecer na página atual...")
        print("🔄 Procurando pelo link 'Download' do relatório...")
        
        download_link_selector = 'a:has-text("Download")' 
        
        max_attempts = 20  # Mais tentativas já que aguardamos na mesma página
        file_path = None
        
        for i in range(max_attempts):
            try:
                print(f"🔄 Tentativa {i+1}/{max_attempts} - Procurando link 'Download'...")
                
                # Aguarda o link de download aparecer
                download_link = page.locator(download_link_selector).first
                await download_link.wait_for(state='visible', timeout=10000)
                
                if await download_link.is_enabled():
                    print(f"✅ Link 'Download' encontrado e clicável após {i+1} tentativas!")
                    
                    # Tira screenshot antes de baixar
                    await page.screenshot(path="debug_before_download.png", full_page=True)
                    print("📸 Screenshot antes do download salvo: debug_before_download.png")
                    
                    # Baixa o arquivo
                    async with page.expect_download() as download_info:
                        await download_link.click()
                        print("✅ Link 'Download' clicado.")
                    
                    download = await download_info.value
                    file_path = os.path.join(downloads_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    print(f"✅ Relatório baixado com sucesso: {file_path}")
                    break
                else:
                    print(f"⏳ Link 'Download' visível, mas não habilitado. Aguardando...")
                    await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                    
            except TimeoutError:
                print(f"⏳ Link 'Download' não visível na tentativa {i+1}/{max_attempts}. Aguardando...")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
            except Exception as e:
                print(f"❌ Erro inesperado na tentativa {i+1}/{max_attempts}: {e}")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
        else:
            print(f"❌ Erro: Link 'Download' não apareceu após {max_attempts} tentativas.")
            await page.screenshot(path="debug_download_link_not_available.png", full_page=True)
            print("📸 Screenshot de erro salvo: debug_download_link_not_available.png")
            await browser.close()
            return

        # --- ETAPA 9: PROCESSAR ARQUIVO E INSERIR NO SUPABASE ---
        print("\n" + "="*70)
        print("🔄 PROCESSANDO ARQUIVO BAIXADO E INSERINDO NO SUPABASE")
        print("="*70)
        
        if file_path:
            print(f"📁 Arquivo baixado: {file_path}")
            
            # Processar o arquivo Excel
            df_processed = await process_excel_file(file_path)
            
            if df_processed is not None and not df_processed.empty:
                # Inserir no Supabase
                success = await insert_data_to_supabase(df_processed, "agenda_base")
                if success:
                    print("✅ Dados inseridos no Supabase com sucesso!")
                else:
                    print("❌ Falha ao inserir dados no Supabase.")
                    print("💾 Salvando dados localmente como backup...")
                    
                    # Salvar como backup local
                    backup_file = f"backup_agenda_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    backup_path = os.path.join(downloads_dir, backup_file)
                    df_processed.to_excel(backup_path, index=False)
                    print(f"📁 Backup salvo em: {backup_path}")
                    print("🔄 Dados processados com sucesso, mas não inseridos no Supabase.")
            else:
                print("❌ Arquivo vazio ou erro no processamento.")
        else:
            print("❌ Nenhum arquivo foi baixado.")

        # --- PARADA AQUI PARA INSPEÇÃO FINAL ---
        print("\n" + "="*70)
        print("🎯 SCRIPT PARADO APÓS DOWNLOAD DO RELATÓRIO")
        print("="*70)
        print("✅ Processo completo realizado com sucesso!")
        print("🔍 Login, seleção de licença, geração e download do relatório")
        print(f"📍 URL atual: {page.url}")
        if file_path:
            print(f"📁 Arquivo baixado: {file_path}")
        print("\n📸 Screenshots disponíveis:")
        print("   - debug_initial_page.png")
        print("   - debug_after_username_fill.png") 
        print("   - debug_after_final_login_click.png")
        print("   - debug_license_selection_page.png")
        print("   - debug_post_login_page.png")
        print("   - debug_report_page_loaded.png")
        print("   - debug_before_generate_click.png")
        print("   - debug_after_generate_click.png")
        print("   - debug_after_report_generation.png")
        print("   - debug_before_download.png")
        print("\n🔍 INSTRUÇÕES:")
        print("   1. Inspecione a página atual no navegador")
        print("   2. Verifique se o relatório foi baixado corretamente")
        print("   3. Me informe se há mais alguma alteração necessária")
        print("\n⏸️  Pressione Ctrl+C para parar o script")
        print("="*70)
        
        # Manter o navegador aberto para inspeção (apenas em modo local)
        if not headless_mode:
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                print("\n🛑 Script interrompido pelo usuário")
        
        await browser.close()
        return

        # --- CÓDIGO REMOVIDO TEMPORARIAMENTE PARA INSPEÇÃO ---
        # Todo o código após o login foi removido para permitir inspeção
        # Será restaurado após identificar as alterações necessárias

# --- NOVA FUNÇÃO PARA TESTAR APENAS A INSERÇÃO NO SUPABASE ---
async def test_supabase_insertion():
    print("\n--- INICIANDO TESTE DE INSERÇÃO NO SUPABASE ---")

    # --- ATENÇÃO: Defina o caminho completo para o arquivo Excel/CSV existente ---
    # Exemplo: 'downloads/1. Relatório diário de publicações (51).xlsx'
    # CERTIFIQUE-SE DE QUE ESTE ARQUIVO EXISTE NA SUA PASTA 'downloads'!
    existing_file_name = "1. Relatório diário de publicações (51).xlsx" # <--- AJUSTE O NOME DO SEU ARQUIVO AQUI
    file_path = os.path.join(downloads_dir, existing_file_name)

    if not os.path.exists(file_path):
        print(f"ERRO: Arquivo '{file_path}' não encontrado. Por favor, verifique o nome do arquivo ou se ele está na pasta 'downloads'.")
        return

    # 1. Ler o arquivo Excel/CSV
    df_report = read_excel_file(file_path)

    if df_report is not None and not df_report.empty:
        # 1.1. Renomear colunas do DataFrame para corresponder ao Supabase
        print("Realizando mapeamento e renomeação de colunas...")
        column_mapping = {
            'Pasta': 'lo_pasta',
            'Número de CNJ': 'lo_numerocnj',
            'Número antigo': 'lo_numeroantigo', # <- Tratamento para esta coluna
            'Outro número': 'lo_outronumero',   # <- Tratamento para esta coluna
            'Cliente principal': 'lo_cliente',
            'Contrário principal': 'lo_contrario',
            'Ação': 'lo_acao',
            'Data da publicação': 'data_publicacao', 
            'Andamentos / Tipo': 'lo_tipoandamento',
            'Teor da publicação': 'lo_descricao',
            'Id': 'lo_idpubli',
        }
        df_report = df_report.rename(columns=column_mapping, errors='ignore') 
        print("Colunas renomeadas. Novas colunas do DataFrame:")
        print(df_report.columns.tolist())

        # --- TRATAMENTO: Converter colunas para string ---
        columns_to_convert_to_str = ['lo_numeroantigo', 'lo_outronumero']
        for col_name in columns_to_convert_to_str:
            if col_name in df_report.columns:
                print(f"Convertendo coluna '{col_name}' para string...")
                # Preenche valores NaN com uma string vazia antes de converter para str
                df_report[col_name] = df_report[col_name].fillna('').astype(str)
                print(f"Coluna '{col_name}' convertida. Novo tipo: {df_report[col_name].dtype}")
            else:
                print(f"Aviso: Coluna '{col_name}' não encontrada no DataFrame para conversão.")
        # --- FIM DO TRATAMENTO ---

        # 1.2. Adicionar nova coluna com valor fixo
        print("Adicionando coluna 'origem_dados' com valor fixo 'LegalOne'...")
        df_report['origem_dados'] = 'LegalOne' 
        print("Coluna 'origem_dados' adicionada. Colunas finais do DataFrame:")
        print(df_report.columns.tolist())

        # 2. Inserir no Supabase
        supabase_table_name = "agenda_base"
        success = await insert_data_to_supabase(df_report, supabase_table_name)
        if success:
            print("Processamento e inserção no Supabase concluídos!")
        else:
            print("Falha no processamento e inserção no Supabase.")
    elif df_report is not None and df_report.empty:
        print("O arquivo de teste está vazio, nada para inserir no Supabase.")
    else:
        print("Não foi possível ler o arquivo de teste, pulando a inserção no Supabase.")

    print("--- TESTE DE INSERÇÃO NO SUPABASE CONCLUÍDO ---")


# --- Execução principal do script ---
if __name__ == "__main__":
    # Para rodar o teste de inserção no Supabase:
    # asyncio.run(test_supabase_insertion())

    # Para rodar a automação COMPLETA (descomente a linha abaixo e comente a de cima):
    asyncio.run(run())
