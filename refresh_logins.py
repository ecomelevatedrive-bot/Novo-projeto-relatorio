"""
Refresh de logins: abre cada perfil Dolphin com tag Shopee,
navega ao Seller Center e aguarda login manual se a sessão expirou.
Objetivo: garantir que todos os cookies estejam válidos ANTES de rodar relatórios.
"""

import sys
import time
from playwright.sync_api import sync_playwright
from dolphin_browser import listar_perfis_shopee, iniciar_perfil, parar_perfil

SELLER_URL = "https://seller.shopee.com.br/portal/sale"
TIMEOUT = 60_000


def _esta_logado(page) -> bool:
    try:
        url = page.url
        texto = page.evaluate("() => document.body.innerText")
        if "buyer/login" in url or "accounts.shopee.com.br" in url:
            return False
        if "Esqueci minha senha" in texto and "Entrar" in texto:
            return False
        if "ENTRAR" in texto and "Cadastrar" in texto:
            return False
        return True
    except Exception:
        return False


def refresh_perfil(perfil: dict) -> bool:
    nome = perfil["nome"]
    profile_id = perfil["id"]

    print()
    print("─" * 55)
    print(f"  {nome}  (ID: {profile_id})")
    print("─" * 55)

    print(f"  Abrindo perfil...")
    try:
        ws_endpoint = iniciar_perfil(profile_id)
    except Exception as e:
        print(f"  ❌ Falha ao abrir perfil: {e}")
        return False

    time.sleep(3)
    logado = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            page = None
            for pg in context.pages:
                try:
                    if "seller.shopee.com.br" in pg.url:
                        page = pg
                        break
                except Exception:
                    pass
            if page is None:
                page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(SELLER_URL, wait_until="domcontentloaded", timeout=TIMEOUT)
            except Exception:
                pass

            print("  Aguardando página carregar (10s)...")
            time.sleep(10)

            if _esta_logado(page):
                print(f"  ✅ {nome} — sessão válida!")
                logado = True
            else:
                print(f"  ⚠  SESSÃO EXPIRADA — {nome}")
                print(f"  Faça login manualmente no Dolphin Anty agora.")
                print(f"  Aguardando até 3 minutos...")
                print()

                for seg in range(180):
                    time.sleep(1)
                    try:
                        pg_check = page
                        for pg in reversed(context.pages):
                            try:
                                if "seller.shopee.com.br" in pg.url:
                                    pg_check = pg
                                    break
                            except Exception:
                                pass
                        if _esta_logado(pg_check):
                            print(f"  ✅ Login detectado! Aguardando estabilizar (5s)...")
                            time.sleep(5)
                            logado = True
                            break
                    except Exception:
                        pass
                    if seg % 30 == 29:
                        print(f"  Aguardando login... {180 - seg - 1}s restantes")

                if not logado:
                    print(f"  ❌ Tempo esgotado — {nome} continua deslogado.")

            try:
                browser.close()
            except Exception:
                pass

    except Exception as e:
        print(f"  ❌ Erro ao verificar {nome}: {e}")

    print(f"  Fechando perfil...")
    parar_perfil(profile_id)
    time.sleep(2)

    return logado


def main():
    filtro = None
    if len(sys.argv) > 2 and sys.argv[1] == "--cliente":
        filtro = sys.argv[2]

    print()
    print("=" * 55)
    print("  REFRESH DE LOGINS — DOLPHIN ANTY / SHOPEE")
    print("=" * 55)
    print("  Abre cada perfil, verifica sessão e aguarda login")
    print("  se necessário. Nenhum relatório será gerado.")
    print("=" * 55)

    print("\n[Dolphin] Buscando perfis com tag 'Shopee'...")
    perfis = listar_perfis_shopee()

    if filtro:
        perfis = [p for p in perfis if p["nome"].lower() == filtro.lower()]

    if not perfis:
        print("\n[Aviso] Nenhum perfil encontrado com a tag 'Shopee'.")
        return

    print(f"  {len(perfis)} perfil(is): {', '.join(p['nome'] for p in perfis)}\n")

    ok = []
    falhas = []

    for perfil in perfis:
        if refresh_perfil(perfil):
            ok.append(perfil["nome"])
        else:
            falhas.append(perfil["nome"])

    print()
    print("=" * 55)
    print(f"  REFRESH CONCLUÍDO")
    print(f"  Logados:    {len(ok)}")
    print(f"  Com falha:  {len(falhas)}")
    if falhas:
        print(f"  Pendentes:  {', '.join(falhas)}")
    print("=" * 55)


if __name__ == "__main__":
    main()
