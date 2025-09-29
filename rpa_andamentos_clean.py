import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

# --- Configuracao da pasta de downloads ---
downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)
print(f"A pasta de downloads sera: {os.path.abspath(downloads_dir)}")

# --- Nome do arquivo de andamentos esperado ---
expected_filename = "z-rpa_andamentos_agenda_rmb_queeue"
print(f"Nome do arquivo esperado: {expected_filename}")

async def close_any_known_popup(page):
    """
    Tenta fechar popups modais ou overlays usando seletores comuns para botoes de fechar.
    Retorna True se um popup foi encontrado e tentado fechar, False caso contrario.
    """
    close_selectors = [
        '[aria-label="Close"]',          # Botao generico de fechar (com label ARIA)
        'button:has-text("Fechar")',     # Botao com texto "Fechar"
        'button:has-text("OK")',         # As vezes "OK" fechar um aviso
        'button.close',                  # Classe comum para botoes de fechar
        '.modal-footer button:has-text("Fechar")', # Botao "Fechar" no rodape de um modal
        '.modal-header button.close',    # Botao "Fechar" no cabecalho de um modal
        '.popup-close',                  # Classe especifica para fechar popups
        '#close-button',                 # ID comum para um botao de fechar
        '[role="dialog"] button:has-text("Fechar")' # Botao fechar dentro de um elemento com role="dialog"
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

async def run():
    async with async_playwright() as p:
        # Configuracao para modo COM interface grafica (para demonstracao)
        headless_mode = False  # Forca modo com interface grafica
        
        print(f"Executando em modo {'headless' if headless_mode else 'com interface grafica'}")
        browser = await p.chromium.launch(headless=headless_mode)
        
        chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" 
        context = await browser.new_context(user_agent=chrome_user_agent)
        
        page = await context.new_page()

        # --- CREDENCIAIS DE LOGIN NO SISTEMA NOVAJUS ---
        USERNAME = "cleiton.sanches@precisionsolucoes.com"
        PASSWORD = "PDS2025@"

        # --- ETAPA 1: NAVEGAR PARA A PAGINA DE LOGIN ---
        novajus_login_url = "https://login.novajus.com.br/conta/login" 
        print(f"Navegando para {novajus_login_url}...")
        
        try:
            await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=60000) 
            print(f"DEBUG: URL atual apos page.goto(): {page.url}")
            await page.screenshot(path="debug_andamentos_initial_page.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_andamentos_initial_page.png' tirada apos page.goto().")
        except TimeoutError:
            print(f"Erro FATAL: page.goto() para {novajus_login_url} excedeu o tempo limite. Verifique sua conexao ou a URL.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para a pagina de login: {e}")
            await browser.close()
            return

        # --- LOGICA PARA CLICAR NO BOTAO ONEPASS (SE PRESENTE) ---
        onepass_selector = '#btn-login-onepass' 
        print(f"Verificando e clicando no botao OnePass '{onepass_selector}' se presente...")
        try:
            onepass_button = page.locator(onepass_selector)
            if await onepass_button.is_visible(timeout=5000): 
                print("Botao OnePass detectado. Clicando...")
                await onepass_button.click()
                await page.wait_for_load_state("domcontentloaded") 
                await page.wait_for_timeout(1000) # Pequena pausa
                print("Clicou em OnePass. Aguardando a tela de login principal.")
                await page.screenshot(path="debug_andamentos_after_onepass_click.png", full_page=True)
            else:
                print("Botao OnePass nao visivel. Prosseguindo.")
        except TimeoutError:
            print("Botao OnePass nao encontrado no tempo esperado. Assumindo que ja esta na tela principal.")
        except Exception as e:
            print(f"Erro ao lidar com o botao OnePass: {e}")

        # --- ETAPA 2: INSERIR E-MAIL ---
        print("Aguardando o campo de e-mail '#Username' aparecer e ficar visivel...")
        try:
            await page.wait_for_selector('#Username', state='visible', timeout=30000)
            print(f"Preenchendo e-mail: {USERNAME}...")
            await page.fill('#Username', USERNAME)
            
            await page.keyboard.press('Tab') 
            print("Pressionado TAB apos preencher o e-mail. Aguardando a tela de senha mudar...")
            
            await page.wait_for_selector('#password', state='visible', timeout=30000) 
            print("Nova tela de senha com ID '#password' detectada.")
            await page.screenshot(path="debug_andamentos_after_username_fill.png", full_page=True)
            
        except TimeoutError:
            print("Erro FATAL: Campo de e-mail '#Username' ou transicao para senha nao ocorreu no tempo esperado.")
            await page.screenshot(path="debug_andamentos_username_or_transition_error.png", full_page=True)
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher e-mail e aguardar transicao: {e}")
            await page.screenshot(path="debug_andamentos_username_fill_error.png", full_page=True)
            await browser.close()
            return

        # --- ETAPA 3: INSERIR SENHA E CLICAR NO BOTAO FINAL DE LOGIN ---
        print("Preenchendo senha no campo '#password'...")
        try:
            await page.fill('#password', PASSWORD)
            print("Senha preenchida.")

            login_button_selector = 'button._button-login-password'
            print(f"Clicando no botao 'Entrar' final '{login_button_selector}'...")
            await page.wait_for_selector(login_button_selector, state='visible', timeout=30000)
            await page.click(login_button_selector)
            print("Botao 'Entrar' final clicado.")

            print("Aguardando o carregamento completo da pagina apos o login (networkidle)...")
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            await page.screenshot(path="debug_andamentos_after_final_login_click.png", full_page=True)
            print("DEBUG: Captura de tela 'debug_andamentos_after_final_login_click.png' tirada apos o login.")
            print(f"DEBUG: URL atual apos login: {page.url}")

        except TimeoutError:
            print("Erro FATAL: Campo de senha '#password' ou botao de login final nao apareceu/clicavel no tempo esperado OU a pagina apos o login nao carregou totalmente.")
            await page.screenshot(path="debug_andamentos_password_field_or_final_button_missing.png", full_page=True)
            print("Navegador mantido aberto para inspecao. Verifique a URL e o conteudo da pagina.")
            if not headless_mode:
                await asyncio.Event().wait()
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao preencher senha ou clicar no botao final: {e}")
            await page.screenshot(path="debug_andamentos_password_fill_or_final_click_error.png", full_page=True)
            print("Navegador mantido aberto para inspecao. Verifique a URL e o conteudo da pagina.")
            if not headless_mode:
                await asyncio.Event().wait()
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 4: SELECAO DA NOVA LICENCA ---
        print("Aguardando pagina de selecao de licenca carregar...")
        await page.wait_for_timeout(3000)
        
        # Tira screenshot da pagina de selecao de licenca
        await page.screenshot(path="debug_andamentos_license_selection_page.png", full_page=True)
        print("Screenshot da pagina de selecao de licenca salvo: debug_andamentos_license_selection_page.png")

        # --- SELECAO DA LICENCA CORRETA USANDO CURRENT-VALUE ---
        print("Selecionando a licenca usando current-value...")
        try:
            # Valor especifico da licenca (robertomatos - cleiton.sanches)
            license_specific_value = "64ee2867d98cf01183cb12fc83a1b95d"
            
            # Seletor para o saf-radio com o current-value especifico
            license_selector = f'saf-radio[current-value="{license_specific_value}"] >> input[part="control"]'
            
            print(f"Valor da licenca: {license_specific_value}")
            print(f"Seletor: {license_selector}")
            print("Aguardando e clicando na licenca especifica...")
            
            # Aguarda o elemento estar visivel
            await page.wait_for_selector(license_selector, state='visible', timeout=30000)
            
            # Clica na licenca especifica
            await page.click(license_selector)
            print("Licenca 'robertomatos - cleiton.sanches' selecionada com sucesso!")

        except TimeoutError:
            print(f"Erro: Licenca com current-value '{license_specific_value}' nao encontrada.")
            await page.screenshot(path="debug_andamentos_license_current_value_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_license_current_value_not_found.png")
            print("Verifique se a licenca esta visivel na pagina.")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao selecionar a licenca: {e}")
            await page.screenshot(path="debug_andamentos_license_current_value_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_license_current_value_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # Clicar no botao 'Continuar' apos selecionar a licenca
        print("Clicando no botao 'Continuar' apos selecionar a licenca...")
        try:
            continue_button_selector = 'saf-button.PersonaSelectionPage-button[type="submit"]' 
            await page.wait_for_selector(continue_button_selector, state='visible', timeout=30000)
            await page.click(continue_button_selector)
            print("Botao 'Continuar' clicado com sucesso!")

        except TimeoutError:
            print(f"Erro: Botao 'Continuar' nao encontrado.")
            await page.screenshot(path="debug_andamentos_continue_button_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_continue_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao clicar no botao continuar: {e}")
            await page.screenshot(path="debug_andamentos_continue_button_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_continue_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 5: ESPERA DA PAGINA POS-LOGIN COMPLETO ---
        print("Aguardando a pagina inicial do sistema carregar...")
        await page.wait_for_load_state("networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        print(f"URL atual apos login completo: {page.url}")
        await page.screenshot(path="debug_andamentos_post_login_page.png", full_page=True)
        print("Screenshot da pagina pos-login salvo: debug_andamentos_post_login_page.png")

        await close_any_known_popup(page)

        # --- ETAPA 6: NAVEGAR PARA O RELATORIO DE ANDAMENTOS ---
        report_url = "https://robertomatos.novajus.com.br/agenda/GenericReport/?id=672"
        print(f"Navegando para o relatorio de andamentos: {report_url}...")
        try:
            await page.goto(report_url, wait_until="domcontentloaded", timeout=60000)
            print(f"URL atual apos navegar para o relatorio: {page.url}")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="debug_andamentos_report_page_loaded.png", full_page=True)
            print("Screenshot da pagina do relatorio salvo: debug_andamentos_report_page_loaded.png")
        except TimeoutError:
            print(f"Erro: Pagina do relatorio nao carregou no tempo esperado.")
            await page.screenshot(path="debug_andamentos_report_page_load_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_report_page_load_error.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao navegar para o relatorio: {e}")
            await page.screenshot(path="debug_andamentos_report_page_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_report_page_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 7: CLICAR NO BOTAO GERAR ---
        print("Testando o botao 'Gerar' do relatorio de andamentos...")
        try:
            generate_button_selector = 'button[name="ButtonSave"][type="submit"]'
            print(f"Seletor do botao: {generate_button_selector}")
            print("Aguardando o botao 'Gerar' aparecer...")
            
            # Aguarda o botao estar visivel
            await page.wait_for_selector(generate_button_selector, state='visible', timeout=30000)
            
            # Tira screenshot antes de clicar
            await page.screenshot(path="debug_andamentos_before_generate_click.png", full_page=True)
            print("Screenshot antes de clicar no botao 'Gerar' salvo: debug_andamentos_before_generate_click.png")
            
            # Clica no botao Gerar
            await page.click(generate_button_selector)
            print("Botao 'Gerar' clicado com sucesso!")
            
            # Aguarda um pouco para ver o resultado
            await page.wait_for_timeout(3000)
            
            # Tira screenshot apos clicar
            await page.screenshot(path="debug_andamentos_after_generate_click.png", full_page=True)
            print("Screenshot apos clicar no botao 'Gerar' salvo: debug_andamentos_after_generate_click.png")
            
            # --- AGUARDAR GERACAO DO RELATORIO ---
            print("Aguardando a geracao do relatorio ser concluida...")
            print("Isso pode levar alguns minutos...")
            
            # Aguarda um tempo maior para a geracao
            await page.wait_for_timeout(10000)  # 10 segundos inicial
            
            # Aguarda a pagina estabilizar (networkidle)
            try:
                await page.wait_for_load_state("networkidle", timeout=120000)  # 2 minutos
                print("Pagina estabilizada apos geracao do relatorio.")
            except TimeoutError:
                print("Timeout aguardando estabilizacao da pagina, mas continuando...")
            
            # Aguarda mais um tempo para garantir que o relatorio foi gerado
            await page.wait_for_timeout(5000)  # 5 segundos adicionais
            
            # Tira screenshot apos aguardar a geracao
            await page.screenshot(path="debug_andamentos_after_report_generation.png", full_page=True)
            print("Screenshot apos aguardar geracao salvo: debug_andamentos_after_report_generation.png")
            print("Aguardou a geracao do relatorio ser concluida.")
            
        except TimeoutError:
            print(f"Erro: Botao 'Gerar' nao encontrado.")
            await page.screenshot(path="debug_andamentos_generate_button_not_found.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_generate_button_not_found.png")
            await browser.close()
            return
        except Exception as e:
            print(f"Erro inesperado ao clicar no botao 'Gerar': {e}")
            await page.screenshot(path="debug_andamentos_generate_button_error.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_generate_button_error.png")
            await browser.close()
            return

        await close_any_known_popup(page)

        # --- ETAPA 8: AGUARDAR RELATORIO APARECER E BAIXAR ---
        print("Aguardando o relatorio ser gerado e aparecer na pagina atual...")
        print("Procurando pelo link 'Download' do relatorio...")
        
        download_link_selector = 'a:has-text("Download")' 
        
        max_attempts = 20  # Mais tentativas ja que aguardamos na mesma pagina
        file_path = None
        
        for i in range(max_attempts):
            try:
                print(f"Tentativa {i+1}/{max_attempts} - Procurando link 'Download'...")
                
                # Aguarda o link de download aparecer
                download_link = page.locator(download_link_selector).first
                await download_link.wait_for(state='visible', timeout=10000)
                
                if await download_link.is_enabled():
                    print(f"Link 'Download' encontrado e clicavel apos {i+1} tentativas!")
                    
                    # Tira screenshot antes de baixar
                    await page.screenshot(path="debug_andamentos_before_download.png", full_page=True)
                    print("Screenshot antes do download salvo: debug_andamentos_before_download.png")
                    
                    # Baixa o arquivo
                    async with page.expect_download() as download_info:
                        await download_link.click()
                        print("Link 'Download' clicado.")
                    
                    download = await download_info.value
                    file_path = os.path.join(downloads_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    print(f"Relatorio de andamentos baixado com sucesso: {file_path}")
                    
                    # Verificar se o nome do arquivo contem o padrao esperado
                    if expected_filename in download.suggested_filename:
                        print(f"Nome do arquivo correto: contem '{expected_filename}'")
                    else:
                        print(f"Nome do arquivo diferente do esperado:")
                        print(f"   Esperado: {expected_filename}")
                        print(f"   Obtido: {download.suggested_filename}")
                    
                    break
                else:
                    print(f"Link 'Download' visivel, mas nao habilitado. Aguardando...")
                    await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                    
            except TimeoutError:
                print(f"Link 'Download' nao visivel na tentativa {i+1}/{max_attempts}. Aguardando...")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
            except Exception as e:
                print(f"Erro inesperado na tentativa {i+1}/{max_attempts}: {e}")
                await page.wait_for_timeout(5000)  # Aguarda 5 segundos
                
        else:
            print(f"Erro: Link 'Download' nao apareceu apos {max_attempts} tentativas.")
            await page.screenshot(path="debug_andamentos_download_link_not_available.png", full_page=True)
            print("Screenshot de erro salvo: debug_andamentos_download_link_not_available.png")
            await browser.close()
            return

        # --- ETAPA 9: FINALIZACAO ---
        print("\n" + "="*70)
        print("SCRIPT PARADO APOS DOWNLOAD DO RELATORIO DE ANDAMENTOS")
        print("="*70)
        print("Processo completo realizado com sucesso!")
        print("Login, selecao de licenca, geracao e download do relatorio de andamentos")
        print(f"URL atual: {page.url}")
        if file_path:
            print(f"Arquivo baixado: {file_path}")
        print("\nScreenshots disponiveis:")
        print("   - debug_andamentos_initial_page.png")
        print("   - debug_andamentos_after_username_fill.png") 
        print("   - debug_andamentos_after_final_login_click.png")
        print("   - debug_andamentos_license_selection_page.png")
        print("   - debug_andamentos_post_login_page.png")
        print("   - debug_andamentos_report_page_loaded.png")
        print("   - debug_andamentos_before_generate_click.png")
        print("   - debug_andamentos_after_generate_click.png")
        print("   - debug_andamentos_after_report_generation.png")
        print("   - debug_andamentos_before_download.png")
        print("\nINSTRUCOES:")
        print("   1. Inspecione a pagina atual no navegador")
        print("   2. Verifique se o relatorio de andamentos foi baixado corretamente")
        print("   3. O arquivo baixado deve ter o nome: z-rpa_andamentos_agenda_rmb_queeue")
        print("   4. Me informe se ha mais alguma alteracao necessaria")
        print("\nPressione Ctrl+C para parar o script")
        print("="*70)
        
        # Manter o navegador aberto para inspecao (modo com interface grafica)
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nScript interrompido pelo usuario")
        
        await browser.close()
        return

# --- Execucao principal do script ---
if __name__ == "__main__":
    print("RPA ANDAMENTOS RMB - VERSAO LIMPA")
    print("Este script automatiza a extracao do relatorio de andamentos do Legal One/Novajus")
    print("Modo: COM INTERFACE GRAFICA (para demonstracao)")
    print("")
    
    asyncio.run(run())
