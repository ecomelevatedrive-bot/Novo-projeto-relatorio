"""
Controla abertura/fechamento de perfis do Dolphin Anty via API local.
Retorna conexão Playwright pronta para usar.
"""

import time
import requests
import config

DOLPHIN_LOCAL  = "http://localhost:3001"
DOLPHIN_CLOUD  = "https://anty-api.com"

_TIMEOUT_LOCAL  = 60   # segundos para chamadas locais
_TIMEOUT_START  = 120  # segundos para iniciar perfil (pode demorar mais)
_MAX_RETRIES    = 3    # tentativas antes de desistir


def _cloud_headers() -> dict:
    return {"Authorization": f"Bearer {config.DOLPHIN_API_TOKEN}"}


def _verificar_dolphin_ativo() -> None:
    """Verifica se o Dolphin Anty está rodando antes de prosseguir."""
    try:
        requests.get(f"{DOLPHIN_LOCAL}/v1.0/auth/login-with-token",
                     timeout=5)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "\n\n  ❌  DOLPHIN ANTY NÃO ESTÁ ABERTO!\n"
            "  Abra o aplicativo Dolphin Anty e tente novamente.\n"
        )
    except requests.exceptions.ReadTimeout:
        pass  # está rodando mas lento — continua


def listar_perfis_shopee() -> list[dict]:
    """Retorna todos os perfis com a tag 'Shopee' (case-insensitive)."""
    todos = []
    page  = 1
    while True:
        resp = requests.get(
            f"{DOLPHIN_CLOUD}/browser_profiles",
            params={"limit": 100, "page": page},
            headers=_cloud_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data   = resp.json()
        perfis = data.get("data", [])
        todos.extend(perfis)
        if data.get("next_page_url") is None or len(perfis) < 100:
            break
        page += 1

    shopee = []
    for p in todos:
        tags = [t.lower() for t in (p.get("tags") or [])]
        if "shopee" in tags:
            shopee.append({"id": p["id"], "nome": p["name"]})

    return shopee


def _sessao_local() -> requests.Session:
    """Cria sessão autenticada na API local do Dolphin com retry."""
    ultimo_erro = None
    for tentativa in range(1, _MAX_RETRIES + 1):
        try:
            s = requests.Session()
            resp = s.post(
                f"{DOLPHIN_LOCAL}/v1.0/auth/login-with-token",
                json={"token": config.DOLPHIN_API_TOKEN},
                timeout=_TIMEOUT_LOCAL,
            )
            resp.raise_for_status()
            return s
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "\n\n  ❌  DOLPHIN ANTY NÃO ESTÁ ABERTO!\n"
                "  Abra o aplicativo Dolphin Anty e tente novamente.\n"
            )
        except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as e:
            ultimo_erro = e
            if tentativa < _MAX_RETRIES:
                print(f"    [Dolphin] Timeout na autenticação local "
                      f"(tentativa {tentativa}/{_MAX_RETRIES}) — aguardando 10s...")
                time.sleep(10)
        except Exception as e:
            ultimo_erro = e
            if tentativa < _MAX_RETRIES:
                print(f"    [Dolphin] Erro na autenticação local "
                      f"(tentativa {tentativa}/{_MAX_RETRIES}): {e} — aguardando 10s...")
                time.sleep(10)

    raise RuntimeError(
        f"\n\n  ❌  Dolphin Anty não respondeu após {_MAX_RETRIES} tentativas.\n"
        f"  Verifique se o Dolphin está aberto e funcionando.\n"
        f"  Erro: {ultimo_erro}\n"
    )


def _ws_from_data(data: dict, profile_id: int) -> str:
    automation = data.get("automation", {})
    port = automation.get("port")
    ws   = automation.get("wsEndpoint", "")
    if port and ws:
        path = ws if ws.startswith("/") else f"/{ws}"
        return f"ws://127.0.0.1:{port}{path}"
    if port:
        return f"ws://127.0.0.1:{port}"
    raise RuntimeError(f"Dolphin não retornou wsEndpoint: {data}")


def _ws_perfil_ativo(sessao: requests.Session, profile_id: int) -> str:
    """Recupera o wsEndpoint de um perfil que já está rodando."""
    resp = sessao.get(
        f"{DOLPHIN_LOCAL}/v1.0/browser_profiles/{profile_id}",
        timeout=_TIMEOUT_LOCAL,
    )
    if resp.status_code == 200:
        return _ws_from_data(resp.json(), profile_id)
    parar_perfil(profile_id)
    time.sleep(5)
    return iniciar_perfil(profile_id)


def iniciar_perfil(profile_id: int) -> str:
    """
    Inicia o perfil no Dolphin e retorna o wsEndpoint para Playwright.
    Tenta até _MAX_RETRIES vezes com pausa entre tentativas.
    """
    _verificar_dolphin_ativo()

    ultimo_erro = None
    for tentativa in range(1, _MAX_RETRIES + 1):
        try:
            sessao = _sessao_local()
            print(f"    [Dolphin] Iniciando perfil {profile_id} "
                  f"(tentativa {tentativa}/{_MAX_RETRIES})...")

            resp = sessao.get(
                f"{DOLPHIN_LOCAL}/v1.0/browser_profiles/{profile_id}/start",
                params={"automation": 1},
                timeout=_TIMEOUT_START,
            )

            if resp.status_code >= 400:
                try:
                    body = resp.json()
                    code = (body.get("errorObject") or {}).get("code", "")
                except Exception:
                    code = ""

                if code == "E_BROWSER_RUN_DUPLICATE":
                    print(f"    [Dolphin] Perfil {profile_id} já rodando — reutilizando.")
                    return _ws_perfil_ativo(sessao, profile_id)

                raise RuntimeError(
                    f"HTTP {resp.status_code} ao iniciar perfil {profile_id}: "
                    f"{resp.text[:300]}"
                )

            return _ws_from_data(resp.json(), profile_id)

        except RuntimeError:
            raise  # erros de lógica não devem ser retentados
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.Timeout) as e:
            ultimo_erro = e
            if tentativa < _MAX_RETRIES:
                print(f"    [Dolphin] Timeout ao iniciar perfil "
                      f"(tentativa {tentativa}/{_MAX_RETRIES}) — aguardando 15s...")
                parar_perfil(profile_id)
                time.sleep(15)
        except Exception as e:
            ultimo_erro = e
            if tentativa < _MAX_RETRIES:
                print(f"    [Dolphin] Erro ao iniciar perfil "
                      f"(tentativa {tentativa}/{_MAX_RETRIES}): {e} — aguardando 15s...")
                time.sleep(15)

    raise RuntimeError(
        f"\n\n  ❌  Não foi possível iniciar o perfil {profile_id} "
        f"após {_MAX_RETRIES} tentativas.\n"
        f"  Verifique se o Dolphin Anty está aberto e o perfil não está travado.\n"
        f"  Último erro: {ultimo_erro}\n"
    )


def parar_perfil(profile_id: int) -> None:
    try:
        sessao = _sessao_local()
        sessao.get(
            f"{DOLPHIN_LOCAL}/v1.0/browser_profiles/{profile_id}/stop",
            timeout=_TIMEOUT_LOCAL,
        )
    except Exception:
        pass
