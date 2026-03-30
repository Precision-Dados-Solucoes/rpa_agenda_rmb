# -*- coding: utf-8 -*-
"""
Camada defensiva compartilhada: fechar modais/popups que bloqueiam Legal One / Novajus.
Playwright (async). Idempotente; não altera regras de negócio dos RPAs.

Exporta:
  - dismiss_blocking_popups(page) — nome explícito
  - close_any_known_popup(page) — alias para compatibilidade com os robôs existentes
"""

from __future__ import annotations

import re
from typing import Callable, List, Tuple

from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeout

LOG_PREFIX = "[LegalOne popup]"


def _log(msg: str) -> None:
    print(f"{LOG_PREFIX} {msg}")


# Timeouts curtos para não alongar o robô
_VISIBILITY_MS = 1_200
_CLICK_MS = 4_000
_POST_CLICK_MS = 450
_OUTER_ROUNDS = 3
_INNER_ATTEMPTS = 3
_CLEAR_POLL_MS = 200
_CLEAR_MAX_WAIT_MS = 2_500


async def _wait_until_clear(page: Page) -> bool:
    """True se não houver mais bloqueio após curto período."""
    steps = max(1, _CLEAR_MAX_WAIT_MS // _CLEAR_POLL_MS)
    for _ in range(steps):
        if not await _needs_dismiss(page):
            return True
        await page.wait_for_timeout(_CLEAR_POLL_MS)
    return not await _needs_dismiss(page)


async def _modal_or_overlay_visible(page: Page) -> bool:
    try:
        dialogs = page.locator('[role="dialog"]')
        n = await dialogs.count()
        for i in range(min(n, 8)):
            if await dialogs.nth(i).is_visible(timeout=450):
                return True
    except Exception as ex:
        _log(f"(diag) leitura de [role=dialog]: {ex}")

    for sel in (".modal.show", ".modal.in", ".modal.fade.in"):
        try:
            if await page.locator(sel).first.is_visible(timeout=350):
                return True
        except Exception:
            pass

    for sel in (".modal-backdrop.show", ".modal-backdrop.in"):
        try:
            if await page.locator(sel).first.is_visible(timeout=350):
                return True
        except Exception:
            pass

    return False


async def _ok_entendi_visible(page: Page) -> bool:
    """Detecta o botão de confirmação típico sem depender do título do modal."""
    try:
        loc = page.get_by_role("button", name=re.compile(r"ok\s*,\s*entendi", re.IGNORECASE))
        if await loc.first.is_visible(timeout=550):
            return True
    except Exception:
        pass
    try:
        loc = page.locator("button, a[role='button'], [role='button']").filter(
            has_text=re.compile(r"ok\s*,\s*entendi", re.IGNORECASE)
        )
        if await loc.first.is_visible(timeout=550):
            return True
    except Exception:
        pass
    return False


async def _needs_dismiss(page: Page) -> bool:
    if await _modal_or_overlay_visible(page):
        return True
    if await _ok_entendi_visible(page):
        return True
    return False


def _primary_ok_entendi_locators(page: Page) -> List[Locator]:
    """Prioridade 1: confirmação ('Ok, entendi'). Lista extensível."""
    return [
        page.get_by_role("button", name=re.compile(r"ok\s*,\s*entendi", re.IGNORECASE)),
        page.locator("button, a[role='button'], [role='button']").filter(
            has_text=re.compile(r"ok\s*,\s*entendi", re.IGNORECASE)
        ),
    ]


def _close_x_locators(page: Page) -> List[Locator]:
    """Prioridade 2: fechar × / X / btn-close."""
    locs: List[Locator] = [
        page.get_by_role("button", name=re.compile(r"^[×✕]\s*$")),
        page.locator('button:has-text("×")'),
        page.locator('[aria-label="Close"]'),
        page.locator('[aria-label="Fechar"]'),
        page.locator("button.close"),
        page.locator(".btn-close"),
        page.locator('[data-dismiss="modal"]'),
        page.locator('[data-bs-dismiss="modal"]'),
        page.locator(".modal-header button.close"),
        page.locator(".modal-header .btn-close"),
        page.locator(".popup-close"),
        page.locator("#close-button"),
        page.locator('button[title="Fechar"]'),
        page.locator('button[title="Close"]'),
        page.locator(".modal-dialog button.close"),
        page.locator("a.close"),
    ]
    return locs


def _fallback_selector_locators(page: Page) -> List[Tuple[str, Callable[[], Locator]]]:
    """
    Prioridade 3+: seletores legados/genéricos. (rótulo para log, factory)
    Evita XPath longo; fácil acrescentar novos seletores.
    """
    specs: List[str] = [
        'button:has-text("Fechar")',
        'button:has-text("OK")',
        'button:has-text("Entendi")',
        'button:has-text("Continuar")',
        ".modal-footer button:has-text('Fechar')",
        ".modal-footer button:has-text('OK')",
        '[role="dialog"] button:has-text("Fechar")',
        ".fechar",
        'a.close',
    ]
    out: List[Tuple[str, Callable[[], Locator]]] = []
    for sel in specs:
        out.append((sel, lambda s=sel: page.locator(s).first))
    return out


def _backdrop_locators(page: Page) -> List[Locator]:
    return [
        page.locator(".modal-backdrop").first,
        page.locator(".modal-backdrop.show").first,
        page.locator(".dialog-overlay").first,
    ]


async def _try_click_visible(
    page: Page,
    loc: Locator,
    log_attempt: str,
) -> bool:
    try:
        target = loc.first if hasattr(loc, "first") else loc
        if not await target.is_visible(timeout=_VISIBILITY_MS):
            return False
        try:
            if not await target.is_enabled():
                _log(f"Tentativa falhou ({log_attempt}): elemento visível porém desabilitado")
                return False
        except Exception:
            pass
        try:
            await target.scroll_into_view_if_needed(timeout=_CLICK_MS)
        except Exception as ex:
            _log(f"(diag) scroll_into_view: {ex}")
        await target.click(timeout=_CLICK_MS)
        await page.wait_for_timeout(_POST_CLICK_MS)
        return True
    except PlaywrightTimeout:
        return False
    except Exception as ex:
        _log(f"Tentativa falhou ({log_attempt}): {ex}")
        return False


async def _press_escape(page: Page) -> None:
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(320)
    except Exception as ex:
        _log(f"Tentativa ESC registrou erro (não fatal): {ex}")


async def dismiss_blocking_popups(page: Page) -> bool:
    """
    Detecta e fecha popups/modais bloqueantes (ex.: manutenção programada).
    Idempotente: várias chamadas seguidas são seguras.

    Returns:
        True se havia bloqueio detectado e houve tentativa de fechamento ou sumiço confirmado.
        False se não havia popup relevante nesta chamada.
    """
    ever_blocked = False

    for outer in range(_OUTER_ROUNDS):
        if not await _needs_dismiss(page):
            if outer == 0:
                _log("Nenhum popup bloqueante encontrado.")
            break

        if not ever_blocked:
            _log("Popup/modal bloqueante detectado.")
        ever_blocked = True

        for attempt in range(_INNER_ATTEMPTS):
            if not await _needs_dismiss(page):
                _log("Popup sumiu sozinho ou já estava fechado (sucesso).")
                break

            # --- Prioridade 1: Ok, entendi ---
            for loc in _primary_ok_entendi_locators(page):
                if await _try_click_visible(page, loc, 'clique em "Ok, entendi"'):
                    _log('Popup fechado pelo botão "Ok, entendi" (ou equivalente).')
                    if await _wait_until_clear(page):
                        break
                if not await _needs_dismiss(page):
                    break
            if not await _needs_dismiss(page):
                break

            # --- Prioridade 2: × / fechar ---
            for loc in _close_x_locators(page):
                if await _try_click_visible(page, loc, "fechar (× / close / aria-label)"):
                    _log('Popup fechado pelo botão de fechar (× ou equivalente).')
                    if await _wait_until_clear(page):
                        break
                if not await _needs_dismiss(page):
                    break
            if not await _needs_dismiss(page):
                break

            # --- Prioridade 3: botões genéricos ---
            for label, factory in _fallback_selector_locators(page):
                try:
                    floc = factory()
                except Exception as ex:
                    _log(f"Tentativa falhou (factory {label}): {ex}")
                    continue
                if await _try_click_visible(page, floc, f"fallback `{label}`"):
                    _log(f"Popup fechado via seletor genérico ({label}).")
                    if await _wait_until_clear(page):
                        break
                if not await _needs_dismiss(page):
                    break
            if not await _needs_dismiss(page):
                break

            # --- ESC ---
            await _press_escape(page)
            if await _wait_until_clear(page):
                _log("Bloqueio removido após tecla ESC.")
                break

            # --- Backdrop (clique fora) ---
            for bloc in _backdrop_locators(page):
                try:
                    if await bloc.is_visible(timeout=450):
                        if await _try_click_visible(page, bloc, "backdrop/overlay"):
                            _log("Tentativa de fechar via clique em backdrop.")
                            if await _wait_until_clear(page):
                                break
                except Exception:
                    pass
                if not await _needs_dismiss(page):
                    break
            if not await _needs_dismiss(page):
                break

            pass

        if await _needs_dismiss(page):
            _log(
                "Aviso: overlay/modal ainda parece visível após tentativas — revisar seletores ou tela manualmente."
            )

    return ever_blocked


async def close_any_known_popup(page: Page) -> bool:
    """Alias histórico dos RPAs; delega para dismiss_blocking_popups."""
    return await dismiss_blocking_popups(page)
