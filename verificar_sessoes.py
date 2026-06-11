"""
Verifica quais perfis Dolphin Anty estão com sessão ativa no Shopee.
Roda rápido: abre cada perfil, checa URL, fecha.
"""

import time
from playwright.sync_api import sync_playwright
from dolphin_browser import listar_perfis_shopee, iniciar_perfil, parar_perfil

URL_SHOPEE = "https://seller.shopee.com.br"

def checar_perfil(perfil: dict) -> str:
    profile_id = perfil["id"]
    nome       = perfil["nome"]
    try:
        ws = iniciar_perfil(profile_id)
        time.sleep(2)

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws)
            ctx  = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # Navega para o seller center
            try:
                page.goto(f"{URL_SHOPEE}/datacenter/overview", wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            time.sleep(5)

            url   = page.url
            texto = ""
            try:
                texto = page.evaluate("() => document.body.innerText")
            except Exception:
                pass

            if "login" in url.lower() or ("Esqueci minha senha" in texto and "Entrar" in texto):
                status = "❌ EXPIRADA"
            else:
                status = "✅ OK"

            try:
                browser.close()
            except Exception:
                pass

        return status

    except Exception as e:
        return f"⚠ ERRO: {str(e)[:60]}"
    finally:
        parar_perfil(profile_id)
        time.sleep(1)


def main():
    print("Buscando perfis com tag Shopee...")
    perfis = listar_perfis_shopee()
    print(f"{len(perfis)} perfil(is) encontrado(s)\n")
    print(f"  {'Cliente':<35} Status")
    print(f"  {'-'*35} ------")

    expirados = []
    ok        = []

    for perfil in perfis:
        status = checar_perfil(perfil)
        print(f"  {perfil['nome']:<35} {status}")
        if "OK" in status:
            ok.append(perfil["nome"])
        else:
            expirados.append(perfil["nome"])

    print()
    print("=" * 55)
    print(f"  ✅ Prontos para rodar : {len(ok)}")
    print(f"  ❌ Precisam de login  : {len(expirados)}")
    if expirados:
        print()
        print("  Faça login manualmente no Dolphin Anty em:")
        for nome in expirados:
            print(f"    • {nome}")
    print("=" * 55)


if __name__ == "__main__":
    main()
