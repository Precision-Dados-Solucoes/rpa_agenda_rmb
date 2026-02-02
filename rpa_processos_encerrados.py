#!/usr/bin/env python3
"""
RPA Processos Encerrados - Legal One Novajus
- Extrai relatório: https://robertomatos.novajus.com.br/processos/GenericReport/?id=680
- Tratativas de colunas (id, data_sentenca, data_encerramento_resultado_tipo_resultado, status)
- UPDATE na tabela processos_base no MySQL Hostinger (chave: id)
"""

import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
from dotenv import load_dotenv
from hostinger_mysql_helper import update_processos_encerrados

load_dotenv("config.env")

downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)

REPORT_URL = "https://robertomatos.novajus.com.br/processos/GenericReport/?id=680"


def _col(df, *nomes):
    for n in nomes:
        if n in df.columns:
            return n
        low = str(n).strip().lower().replace(" ", "_")
        for c in df.columns:
            if str(c).strip().lower().replace(" ", "_") == low:
                return c
    return None


def process_excel_processos_encerrados(file_path):
    """Lê Excel e prepara DataFrame com id, data_sentenca, data_encerramento_resultado_tipo_resultado, status."""
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
    except Exception as e:
        print(f"Erro ao ler Excel: {e}")
        return None
    id_col = _col(df, "id", "Id", "ID")
    if not id_col:
        print("Coluna 'id' não encontrada no relatório.")
        return None
    df = df.copy()
    df["id"] = pd.to_numeric(df[id_col], errors="coerce")
    df = df[df["id"].notna()].copy()
    # Renomear para o que o helper espera (se vier com outro nome)
    for sup, names in [
        ("data_sentenca", ["data_sentenca", "data sentenca"]),
        ("data_encerramento_resultado_tipo_resultado", ["data_encerramento_resultado_tipo_resultado", "data_encerramento", "data encerramento resultado tipo resultado"]),
        ("status", ["status", "Status"]),
    ]:
        c = _col(df, *names)
        if c is not None and c != sup:
            df[sup] = df[c]
    return df


async def close_any_known_popup(page):
    for selector in ['[aria-label="Close"]', 'button:has-text("Fechar")', 'button:has-text("OK")']:
        try:
            el = page.locator(selector)
            if await el.is_visible(timeout=1000):
                await el.click(timeout=3000)
                await page.wait_for_timeout(500)
                return True
        except Exception:
            pass
    return False


async def run():
    async with async_playwright() as p:
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            headless_mode = True
        browser_args = []
        if headless_mode:
            browser_args = ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        browser = await p.chromium.launch(headless=headless_mode, args=browser_args)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36")
        page = await context.new_page()

        USERNAME = os.getenv("NOVAJUS_USERNAME", "cleiton.sanches@precisionsolucoes.com")
        PASSWORD = os.getenv("NOVAJUS_PASSWORD", "PDS2025@")
        novajus_login_url = "https://login.novajus.com.br/conta/login"

        try:
            await page.goto(novajus_login_url, wait_until="domcontentloaded", timeout=120000)
        except Exception as e:
            print(f"Erro ao navegar para login: {e}")
            await browser.close()
            return

        try:
            onepass = page.locator('#btn-login-onepass')
            if await onepass.is_visible(timeout=5000):
                await onepass.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        try:
            await page.wait_for_selector('#Username', state='visible', timeout=30000)
            await page.fill('#Username', USERNAME)
            await page.keyboard.press('Tab')
            await page.wait_for_selector('#password', state='visible', timeout=30000)
            await page.fill('#password', PASSWORD)
            await page.wait_for_selector('button._button-login-password', state='visible', timeout=30000)
            await page.click('button._button-login-password')
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Erro no login: {e}")
            await browser.close()
            return

        await close_any_known_popup(page)
        await page.wait_for_timeout(3000)

        try:
            license_value = "64ee2867d98cf01183cb12fc83a1b95d"
            license_selector = f'saf-radio[current-value="{license_value}"] >> input[part="control"]'
            await page.wait_for_selector(license_selector, state='visible', timeout=30000)
            await page.click(license_selector)
            await page.wait_for_selector('saf-button.PersonaSelectionPage-button[type="submit"]', state='visible', timeout=30000)
            await page.click('saf-button.PersonaSelectionPage-button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Erro ao selecionar licença: {e}")
            await browser.close()
            return

        await close_any_known_popup(page)
        print(f"Navegando para relatório Processos Encerrados: {REPORT_URL}")
        try:
            await page.goto(REPORT_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Erro ao abrir relatório: {e}")
            await browser.close()
            return

        try:
            await page.wait_for_selector('button[name="ButtonSave"][type="submit"]', state='visible', timeout=30000)
            await page.click('button[name="ButtonSave"][type="submit"]')
            await page.wait_for_timeout(10000)
            await page.wait_for_load_state("networkidle", timeout=120000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Erro ao clicar em Gerar: {e}")
            await browser.close()
            return

        download_link_selector = 'a:has-text("Download")'
        file_path = None
        for i in range(20):
            try:
                link = page.locator(download_link_selector).first
                await link.wait_for(state='visible', timeout=10000)
                if await link.is_enabled():
                    async with page.expect_download() as download_info:
                        await link.click()
                    download = await download_info.value
                    file_path = os.path.join(downloads_dir, download.suggested_filename)
                    await download.save_as(file_path)
                    print(f"Relatório baixado: {file_path}")
                    break
            except Exception:
                await page.wait_for_timeout(5000)
        else:
            print("Link Download não apareceu.")
            await browser.close()
            return

        if file_path and os.path.isfile(file_path):
            df = process_excel_processos_encerrados(file_path)
            if df is not None and not df.empty:
                print(f"Atualizando {len(df)} registros em processos_base (Hostinger)...")
                ok = update_processos_encerrados(df, "processos_base")
                if ok:
                    print("Processos encerrados atualizados no MySQL Hostinger com sucesso.")
                else:
                    print("Falha ao atualizar no MySQL Hostinger.")
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            else:
                print("Nenhum dado válido no relatório.")
        await browser.close()
        print("RPA Processos Encerrados finalizado.")


if __name__ == "__main__":
    asyncio.run(run())
