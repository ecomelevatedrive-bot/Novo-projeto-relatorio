"""
Lê perfis do Dolphin Anty via API na nuvem e extrai credenciais Shopee das notas.

Formato esperado no campo Notas de cada perfil Dolphin:
{"partner_id": 123456, "partner_key": "sua_key", "shop_id": 789, "access_token": "token"}

Perfis sem notas válidas são ignorados automaticamente.
"""

import json
import requests
import config

DOLPHIN_CLOUD_API = "https://anty-api.com"


def _listar_perfis() -> list[dict]:
    """Busca todos os perfis via API na nuvem do Dolphin Anty."""
    todos = []
    page  = 1
    while True:
        resp = requests.get(
            f"{DOLPHIN_CLOUD_API}/browser_profiles",
            params={"limit": 100, "page": page},
            headers={"Authorization": f"Bearer {config.DOLPHIN_API_TOKEN}"},
            timeout=15,
        )
        resp.raise_for_status()
        data     = resp.json()
        perfis   = data.get("data", [])
        todos.extend(perfis)

        if data.get("next_page_url") is None or len(perfis) < 100:
            break
        page += 1

    return todos


def _extrair_credenciais(perfil: dict) -> dict | None:
    """Extrai credenciais Shopee do campo notes do perfil."""
    notes_raw = perfil.get("notes")

    # Notes pode ser string, dict com "content", ou None
    if isinstance(notes_raw, dict):
        content = notes_raw.get("content") or ""
    elif isinstance(notes_raw, str):
        content = notes_raw
    else:
        return None

    content = content.strip()
    if not content:
        return None

    try:
        creds = json.loads(content)
    except json.JSONDecodeError:
        return None

    obrigatorios = {"partner_id", "partner_key", "shop_id", "access_token"}
    if not obrigatorios.issubset(creds.keys()):
        return None

    if not creds["partner_id"] or not creds["partner_key"]:
        return None

    return {
        "partner_id":   int(creds["partner_id"]),
        "partner_key":  str(creds["partner_key"]),
        "shop_id":      int(creds["shop_id"]),
        "access_token": str(creds["access_token"]),
    }


def carregar_clientes_do_dolphin() -> list[dict]:
    """
    Lê todos os perfis do Dolphin Anty e retorna lista de clientes
    com credenciais Shopee extraídas das notas.
    """
    print("[Dolphin] Buscando perfis via API na nuvem...")
    try:
        perfis = _listar_perfis()
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao conectar na API do Dolphin: {e}")
        return []

    clientes  = []
    ignorados = []

    for perfil in perfis:
        nome  = perfil.get("name", f"Perfil {perfil.get('id')}")
        creds = _extrair_credenciais(perfil)
        if creds:
            clientes.append({"nome": nome, **creds})
        else:
            ignorados.append(nome)

    print(f"[Dolphin] {len(perfis)} perfis encontrados → "
          f"{len(clientes)} com credenciais Shopee, {len(ignorados)} sem credenciais.")

    return clientes
