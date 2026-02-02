#!/usr/bin/env python3
"""
RPA Processos Novos - Legal One Novajus
- Extrai relatório: https://robertomatos.novajus.com.br/processos/GenericReport/?id=679
- Tratativas de colunas (id, link, data_cadastro)
- INSERT na tabela processos_base no MySQL Hostinger
"""

import asyncio
import os
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
from dotenv import load_dotenv
from hostinger_mysql_helper import insert_processos_base

load_dotenv("config.env")

downloads_dir = "downloads"
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)

REPORT_URL = "https://robertomatos.novajus.com.br/processos/GenericReport/?id=679"


def _col(df, *nomes):
    for n in nomes:
        if n in df.columns:
            return n
        low = str(n).strip().lower().replace(" ", "_")
        for c in df.columns:
            if str(c).strip().lower().replace(" ", "_") == low:
                return c
    return None


def _parse_data_apenas(val):
    if val is None or pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp) and pd.notna(val):
        return val.strftime("%Y-%m-%d 00:00:00")
    s = str(val).strip()
    if not s:
        return None
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            dt = pd.to_datetime(s, format=fmt, errors="raise")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d 00:00:00")
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d 00:00:00")
    except Exception:
        pass
    return None


def process_excel_processos_novos(file_path):
    """Lê Excel e prepara DataFrame para processos_base (id, link, data_cadastro)."""
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
    col_cadastro = _col(df, "data_cadastro", "data cadastro")
    if col_cadastro is not None:
        df["data_cadastro"] = df[col_cadastro].apply(_parse_data_apenas)
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
        print(f"Navegando para relatório Processos Novos: {REPORT_URL}")
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
            df = process_excel_processos_novos(file_path)
            if df is not None and not df.empty:
                print(f"Processando {len(df)} registros para processos_base (Hostinger)...")
                ok = insert_processos_base(df, "processos_base")
                if ok:
                    print("Processos novos inseridos no MySQL Hostinger com sucesso.")
                else:
                    print("Falha ao inserir no MySQL Hostinger.")
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            else:
                print("Nenhum dado válido no relatório.")
        await browser.close()
        print("RPA Processos Novos finalizado.")


if __name__ == "__main__":
    asyncio.run(run())
