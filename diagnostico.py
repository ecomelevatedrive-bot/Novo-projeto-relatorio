"""
Diagnóstico: mostra todos os elementos clicáveis da página Business Insights
para identificar o texto exato do seletor de período.
"""
import json
import time
from datetime import date, datetime, timedelta
import config
from dolphin_browser import listar_perfis_shopee, iniciar_perfil, parar_perfil


def main():
    perfis = listar_perfis_shopee()
    if not perfis:
        print("Nenhum perfil com tag Shopee encontrado.")
        return

    print(f"Perfis: {[p['nome'] for p in perfis]}")
    perfil = perfis[0]
    print(f"Usando: {perfil['nome']}")

    ws = iniciar_perfil(perfil["id"])
    time.sleep(5)

    try:
        from playwright.sync_api import sync_playwright

        hoje     = date.today()
        ontem    = hoje - timedelta(days=1)
        inicio   = ontem - timedelta(days=6)
        end_ts   = int(datetime(ontem.year, ontem.month, ontem.day, 23, 59, 59).timestamp())
        start_ts = int(datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0).timestamp())

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page    = context.new_page()

            print("\n[1] Navegando para Business Insights...")
            page.goto("https://seller.shopee.com.br/datacenter/overview?ADTAG=sidebar",
                      wait_until="domcontentloaded", timeout=90_000)
            time.sleep(15)
            page.screenshot(path="diag_business_inicial.png")

            url_atual = page.url
            texto = page.evaluate("() => document.body.innerText")
            logado = "Esqueci minha senha" not in texto and "buyer/login" not in url_atual
            print(f"URL: {url_atual}")
            print(f"Logado: {'SIM ✓' if logado else 'NÃO ✗ — faça login no Dolphin!'}")

            if not logado:
                print("SESSÃO EXPIRADA.")
                return

            # Lista todos os textos clicáveis presentes na página
            print("\n[2] Elementos clicáveis na página:")
            elementos = page.evaluate("""
                () => {
                    const tags = ['button', 'li', 'span', 'div', 'a', 'label'];
                    const vistos = new Set();
                    const result = [];
                    for (const tag of tags) {
                        for (const el of document.querySelectorAll(tag)) {
                            const t = el.textContent.trim();
                            const rect = el.getBoundingClientRect();
                            if (t && t.length < 50 && t.length > 1 &&
                                rect.width > 0 && rect.height > 0 &&
                                !vistos.has(t)) {
                                vistos.add(t);
                                result.push({ tag: el.tagName, texto: t });
                            }
                        }
                    }
                    return result;
                }
            """)

            print("  Textos curtos visíveis:")
            for el in elementos:
                print(f"    <{el['tag'].lower()}> '{el['texto']}'")

            with open("diag_elementos.json", "w", encoding="utf-8") as f:
                json.dump(elementos, f, ensure_ascii=False, indent=2)
            print(f"\n  Total: {len(elementos)} elementos. Salvos em diag_elementos.json")

            print("\n[3] Testando API Business...")
            resp = page.evaluate(f"""
                async () => {{
                    const r = await fetch('https://seller.shopee.com.br/api/mydata/v3/dashboard/key-metrics/?period=past7days', {{
                        credentials: 'include',
                        headers: {{ 'accept': 'application/json', 'x-requested-with': 'XMLHttpRequest' }}
                    }});
                    return await r.json();
                }}
            """)
            print(f"  code: {resp.get('code')}")
            print(f"  result keys: {list((resp.get('result') or {}).keys())}")
            paid_gmv = (resp.get('result') or {}).get('paid_gmv')
            paid_ord = (resp.get('result') or {}).get('paid_orders')
            print(f"  paid_gmv: {paid_gmv}")
            print(f"  paid_orders: {paid_ord}")
            with open("diag_business_api.json", "w", encoding="utf-8") as f:
                json.dump(resp, f, ensure_ascii=False, indent=2)

            print("\n[4] Navegando para ADS...")
            page.goto("https://seller.shopee.com.br/portal/marketing/pas/index",
                      wait_until="domcontentloaded", timeout=90_000)
            time.sleep(15)
            page.screenshot(path="diag_ads_inicial.png")

            elementos_ads = page.evaluate("""
                () => {
                    const tags = ['button', 'li', 'span', 'div', 'a', 'label'];
                    const vistos = new Set();
                    const result = [];
                    for (const tag of tags) {
                        for (const el of document.querySelectorAll(tag)) {
                            const t = el.textContent.trim();
                            const rect = el.getBoundingClientRect();
                            if (t && t.length < 50 && t.length > 1 &&
                                rect.width > 0 && rect.height > 0 &&
                                !vistos.has(t)) {
                                vistos.add(t);
                                result.push({ tag: el.tagName, texto: t });
                            }
                        }
                    }
                    return result;
                }
            """)
            print("  Elementos ADS:")
            for el in elementos_ads:
                print(f"    <{el['tag'].lower()}> '{el['texto']}'")

            print(f"\n[5] Testando API ADS (get_time_graph)...")
            resp_ads = page.evaluate(f"""
                async () => {{
                    const r = await fetch('https://seller.shopee.com.br/api/pas/v1/report/get_time_graph/?start_time={start_ts}&end_time={end_ts}&group_type=0&report_type=1', {{
                        credentials: 'include',
                        headers: {{ 'accept': 'application/json', 'x-requested-with': 'XMLHttpRequest' }}
                    }});
                    return await r.json();
                }}
            """)
            print(f"  code: {resp_ads.get('code')}")
            data_ads = resp_ads.get('data') or {}
            slots = data_ads.get('report_by_time') or []
            print(f"  slots: {len(slots)}")
            if slots:
                m = slots[0].get('metrics') or {}
                print(f"  primeiro slot metrics keys: {list(m.keys())}")
            with open("diag_ads_api.json", "w", encoding="utf-8") as f:
                json.dump(resp_ads, f, ensure_ascii=False, indent=2)

            page.close()
            browser.close()

    finally:
        parar_perfil(perfil["id"])

    print("\n✓ Diagnóstico concluído!")
    print("  Verifique: diag_business_inicial.png, diag_ads_inicial.png")
    print("  Verifique: diag_elementos.json, diag_business_api.json, diag_ads_api.json")


if __name__ == "__main__":
    main()
