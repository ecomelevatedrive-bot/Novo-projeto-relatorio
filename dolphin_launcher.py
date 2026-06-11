"""
Integração com Dolphin Anty via API local (porta 3001).

Fluxo:
  1. Busca perfis disponíveis na API local do Dolphin Anty
  2. Inicia o perfil escolhido (retorna porta de automação)
  3. Conecta via Playwright (Chromium remoto) e navega até o relatório HTML
  4. Mantém o browser aberto para o usuário interagir

Pré-requisitos:
  - Dolphin Anty instalado e em execução
  - pip install playwright && playwright install chromium
"""

import os
import time
import requests
from pathlib import Path

DOLPHIN_API = "http://localhost:3001"


# ──────────────────────────────────────────────
#  DOLPHIN ANTY — API LOCAL
# ──────────────────────────────────────────────

def _listar_perfis() -> list[dict]:
    """Retorna lista de perfis cadastrados no Dolphin Anty."""
    resp = requests.get(
        f"{DOLPHIN_API}/v1.0/browser_profiles",
        params={"limit": 50, "page": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def _iniciar_perfil(profile_id: str) -> str:
    """
    Inicia o perfil no Dolphin Anty e retorna o wsEndpoint
    para conexão via Playwright/Selenium.
    """
    resp = requests.get(
        f"{DOLPHIN_API}/v1.0/browser_profiles/{profile_id}/start",
        params={"automation": 1},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    automation = data.get("automation", {})
    port       = automation.get("port")
    ws         = automation.get("wsEndpoint", "")

    if not port and not ws:
        raise RuntimeError(
            f"Dolphin não retornou wsEndpoint para o perfil {profile_id}.\n"
            f"Resposta: {data}"
        )

    if ws:
        return ws
    return f"ws://127.0.0.1:{port}"


def _parar_perfil(profile_id: str) -> None:
    try:
        requests.get(
            f"{DOLPHIN_API}/v1.0/browser_profiles/{profile_id}/stop",
            timeout=10,
        )
    except Exception:
        pass


# ──────────────────────────────────────────────
#  ABERTURA DO RELATÓRIO NO DOLPHIN
# ──────────────────────────────────────────────

def abrir_no_dolphin(caminho_html: str, profile_id: str | None = None) -> None:
    """
    Abre o relatório HTML gerado dentro de um perfil do Dolphin Anty.

    Parâmetros:
        caminho_html : Caminho local do arquivo .html gerado
        profile_id   : ID do perfil Dolphin (None = usa o primeiro disponível)
    """
    # Importa Playwright (deve estar instalado)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright não está instalado.\n"
            "Execute: pip install playwright && playwright install chromium"
        )

    # Resolve perfil
    if not profile_id:
        print("[Dolphin] Buscando perfis disponíveis...")
        perfis = _listar_perfis()
        if not perfis:
            raise RuntimeError(
                "Nenhum perfil encontrado no Dolphin Anty.\n"
                "Crie pelo menos um perfil no aplicativo Dolphin Anty antes de continuar."
            )
        profile_id = str(perfis[0]["id"])
        nome_perfil = perfis[0].get("name", profile_id)
        print(f"[Dolphin] Usando perfil: '{nome_perfil}' (ID: {profile_id})")
    else:
        print(f"[Dolphin] Usando perfil ID: {profile_id}")

    # Inicia o perfil
    print("[Dolphin] Iniciando perfil no Dolphin Anty...")
    ws_endpoint = _iniciar_perfil(profile_id)
    print(f"[Dolphin] Conectado em: {ws_endpoint}")
    time.sleep(2)   # aguarda o browser inicializar

    # Converte caminho para URL file://
    arquivo = Path(caminho_html).resolve()
    url_relatorio = arquivo.as_uri()

    print(f"[Dolphin] Abrindo relatório: {url_relatorio}")

    # Conecta via Playwright e navega
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page    = context.new_page()
        page.goto(url_relatorio)
        page.wait_for_load_state("networkidle")
        print("[Dolphin] Relatório aberto com sucesso!")
        print("[Dolphin] O navegador permanecerá aberto. Feche manualmente quando terminar.")
        # Mantém o processo vivo até o usuário fechar o terminal
        try:
            input("\nPressione ENTER para fechar o browser e encerrar...\n")
        except (EOFError, KeyboardInterrupt):
            pass
        browser.close()

    print(f"[Dolphin] Parando perfil {profile_id}...")
    _parar_perfil(profile_id)
    print("[Dolphin] Encerrado.")
