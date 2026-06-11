"""
Extrai dados do Shopee Seller Center via chamadas JS diretas (fetch).
Compatível com conexão CDP (Dolphin Anty) — não usa interceptors de rede.

Páginas:
  - Business: https://seller.shopee.com.br/datacenter/overview
  - ADS:      https://seller.shopee.com.br/portal/marketing/pas/index
"""

import json
import re
import time
from datetime import date, datetime, timedelta
from playwright.sync_api import Page

TIMEOUT  = 90_000
BASE_URL = "https://seller.shopee.com.br"
URL_BUSINESS = f"{BASE_URL}/datacenter/overview?ADTAG=sidebar"
URL_ADS      = f"{BASE_URL}/portal/marketing/pas/index"


def _timestamps_7_dias() -> tuple[int, int]:
    """Últimos 7 dias completos excluindo hoje. Ex: hoje=20/05 → 13/05–19/05"""
    ontem  = date.today() - timedelta(days=1)
    inicio = ontem - timedelta(days=6)
    end_ts   = int(datetime(ontem.year,  ontem.month,  ontem.day,  23, 59, 59).timestamp())
    start_ts = int(datetime(inicio.year, inicio.month, inicio.day,  0,  0,  0).timestamp())
    return start_ts, end_ts


def _timestamps_semana_anterior() -> tuple[int, int]:
    """7 dias anteriores ao período atual. Ex: hoje=20/05 → 06/05–12/05"""
    ontem       = date.today() - timedelta(days=1)
    fim_ant     = ontem - timedelta(days=7)
    inicio_ant  = fim_ant - timedelta(days=6)
    end_ts   = int(datetime(fim_ant.year,   fim_ant.month,   fim_ant.day,   23, 59, 59).timestamp())
    start_ts = int(datetime(inicio_ant.year, inicio_ant.month, inicio_ant.day, 0,  0,  0).timestamp())
    return start_ts, end_ts


# ──────────────────────────────────────────────────────────────────────────────
# Verificação de sessão
# ──────────────────────────────────────────────────────────────────────────────

def _esta_logado(page: Page) -> bool:
    try:
        url   = page.url
        texto = page.evaluate("() => document.body.innerText")
        if "buyer/login" in url:
            return False
        if "Esqueci minha senha" in texto and "Entrar" in texto:
            return False
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Chamada direta via JS fetch (único método confiável com CDP)
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_api(page: Page, path: str, params: dict | None = None) -> dict:
    qs  = "&".join(f"{k}={v}" for k, v in (params or {}).items())
    url = f"{BASE_URL}{path}?{qs}" if qs else f"{BASE_URL}{path}"

    result = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch({json.dumps(url)}, {{
                    credentials: 'include',
                    headers: {{
                        'accept': 'application/json, text/plain, */*',
                        'x-requested-with': 'XMLHttpRequest',
                        'x-csrftoken': (document.cookie.match(/csrftoken=([^;]+)/) || ['',''])[1]
                    }}
                }});
                if (!r.ok) return {{ _http_error: r.status }};
                return await r.json();
            }} catch(e) {{
                return {{ _fetch_error: e.toString() }};
            }}
        }}
    """)

    if not isinstance(result, dict):
        return {}
    if "_fetch_error" in result:
        err = result["_fetch_error"]
        if "Failed to fetch" in err:
            print(f"    [FETCH ERRO] {err} — possível sessão expirada ou CSP bloqueando {path}")
        else:
            print(f"    [FETCH ERRO] {err}")
    if "_http_error" in result:
        print(f"    [FETCH HTTP {result['_http_error']}] {path}")
    return result


def _post_api(page: Page, path: str, body: dict | None = None) -> dict:
    """Envia POST com JSON body — necessário para endpoints do painel de ADS."""
    url      = f"{BASE_URL}{path}"
    body_str = json.dumps(json.dumps(body or {}))   # JS string literal com JSON interno

    result = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch({json.dumps(url)}, {{
                    method: 'POST',
                    credentials: 'include',
                    headers: {{
                        'accept': 'application/json, text/plain, */*',
                        'content-type': 'application/json',
                        'x-requested-with': 'XMLHttpRequest',
                        'x-csrftoken': (document.cookie.match(/csrftoken=([^;]+)/) || ['',''])[1]
                    }},
                    body: {body_str}
                }});
                if (!r.ok) return {{ _http_error: r.status }};
                return await r.json();
            }} catch(e) {{
                return {{ _fetch_error: e.toString() }};
            }}
        }}
    """)

    if not isinstance(result, dict):
        return {}
    if "_fetch_error" in result:
        err = result["_fetch_error"]
        if "Failed to fetch" in err:
            print(f"    [POST ERRO] {err} — possível sessão expirada ou CSP bloqueando {path}")
        else:
            print(f"    [POST ERRO] {err}")
    if "_http_error" in result:
        print(f"    [POST HTTP {result['_http_error']}] {path}")
    return result


def _salvar_debug(nome: str, dados, page: Page = None) -> None:
    try:
        with open(f"debug_{nome}_api.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    if page:
        try:
            page.screenshot(path=f"debug_{nome}.png", timeout=15_000)
        except Exception:
            pass
        try:
            texto = page.evaluate("() => document.body.innerText")
            with open(f"debug_{nome}_texto.txt", "w", encoding="utf-8") as f:
                f.write(texto or "")
            print(f"    [DEBUG] Página salva em debug_{nome}_texto.txt e debug_{nome}.png")
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Selecionar período na UI
# ──────────────────────────────────────────────────────────────────────────────

def _encontrar_coordenadas(page: Page, textos: list[str]) -> tuple | None:
    """
    Busca o elemento visível com texto exato (ou mais curto que inclui o texto).
    Retorna as coordenadas (cx, cy) do centro do elemento, ou None.
    """
    textos_json = json.dumps([t.strip() for t in textos])
    resultado = page.evaluate(f"""
        () => {{
            const norm = s => s.trim().toLowerCase()
                .normalize('NFD').replace(/[̀-ͯ]/g, '');
            const alvos = {textos_json}.map(norm);

            let melhor = null;
            let melhorLen = Infinity;

            for (const el of document.querySelectorAll('*')) {{
                // Só elementos folha ou quase-folha (sem filhos de texto relevante)
                const filhos = el.childElementCount;
                if (filhos > 3) continue;

                const texto = el.textContent.trim();
                if (!texto || texto.length > 60) continue;

                const textoNorm = norm(texto);
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;

                for (const alvo of alvos) {{
                    if (textoNorm === alvo) {{
                        // Correspondência exata — retorna imediatamente
                        return {{
                            x: rect.left + rect.width / 2,
                            y: rect.top  + rect.height / 2,
                            texto: texto
                        }};
                    }}
                    if (textoNorm.includes(alvo) && texto.length < melhorLen) {{
                        melhor = {{ x: rect.left + rect.width/2, y: rect.top + rect.height/2, texto }};
                        melhorLen = texto.length;
                    }}
                }}
            }}
            return melhor;
        }}
    """)
    if resultado and isinstance(resultado, dict):
        return resultado  # retorna o dict diretamente
    return None


def _mouse_clicar(page: Page, textos: list[str]) -> str:
    """
    Encontra o elemento pelo texto e usa page.mouse.click (mouse real).
    Retorna o texto do elemento clicado, ou "".
    """
    coord = _encontrar_coordenadas(page, textos)
    if not coord:
        return ""
    x     = coord["x"]
    y     = coord["y"]
    texto = coord.get("texto", "")
    page.mouse.move(x, y)
    time.sleep(0.3)
    page.mouse.click(x, y)
    return texto


def _clicar_7_dias_business(page: Page) -> bool:
    """
    Seleciona 'Últimos 7 dias' no Business Insights usando mouse real (page.mouse.click).
    """
    textos_7dias = ["Últimos 7 dias", "últimos 7 dias", "Ultimos 7 dias", "ultimos 7 dias"]
    textos_periodo_ativo = ["Tempo real", "Tempo Real", "tempo real",
                            "Hoje", "hoje", "Ontem", "ontem",
                            "Últimos 30 dias", "últimos 30 dias"]

    for tentativa in range(1, 4):
        print(f"    [BUSINESS] Tentativa {tentativa}: localizando 'Últimos 7 dias'...")

        # Tenta clicar direto
        clicou = _mouse_clicar(page, textos_7dias)
        if clicou:
            print(f"    [BUSINESS] ✓ Mouse clicou em: '{clicou}'")
            return True

        # Abre o seletor clicando no período ativo
        abriu = _mouse_clicar(page, textos_periodo_ativo)
        if abriu:
            print(f"    [BUSINESS] Seletor aberto via '{abriu}', aguardando opções...")
            time.sleep(2)
            clicou = _mouse_clicar(page, textos_7dias)
            if clicou:
                print(f"    [BUSINESS] ✓ Mouse clicou em: '{clicou}'")
                return True

        time.sleep(4)

    # Diagnóstico: lista todos os textos curtos visíveis
    try:
        visiveis = page.evaluate("""
            () => {
                const norm = s => s.trim();
                const res = new Set();
                for (const el of document.querySelectorAll('*')) {
                    const t = norm(el.textContent);
                    const r = el.getBoundingClientRect();
                    if (t && t.length < 40 && r.width > 0 && r.height > 0)
                        res.add(t);
                }
                return [...res].slice(0, 50);
            }
        """)
        print(f"    [BUSINESS] Textos visíveis: {visiveis}")
    except Exception:
        pass

    print("    [BUSINESS] ⚠ Período não selecionado — usando padrão da página.")
    return False


def _clicar_periodo_ads_por_regex(page: Page) -> dict | None:
    """Encontra o elemento do seletor de período ADS que exibe uma data (ex: '15/05 - 22/05')."""
    return page.evaluate("""
        () => {
            const re = /\\d{2}\\/\\d{2}\\s*[-–]\\s*\\d{2}\\/\\d{2}/;
            for (const el of document.querySelectorAll('*')) {
                if (el.childElementCount > 5) continue;
                const txt = el.textContent.trim();
                if (txt.length > 80) continue;
                if (!re.test(txt)) continue;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, texto: txt };
            }
            return null;
        }
    """)


def _clicar_7_dias_ads(page: Page) -> bool:
    """Seleciona 'Última semana' no painel de ADS usando mouse real."""
    textos_semana = ["Última semana", "última semana", "Ultima semana", "ultima semana", "Last week"]
    textos_periodo_ativo = ["Hoje", "hoje", "Ontem", "ontem", "Este mês",
                            "Últimos 30 dias", "Personalizado", "Custom",
                            "Última semana", "Esta semana"]

    for tentativa in range(1, 4):
        print(f"    [ADS] Tentativa {tentativa}: localizando 'Última semana'...")

        clicou = _mouse_clicar(page, textos_semana)
        if clicou:
            print(f"    [ADS] ✓ Mouse clicou em: '{clicou}'")
            return True

        # Tenta abrir pelo período ativo com texto fixo
        abriu = _mouse_clicar(page, textos_periodo_ativo)
        if abriu:
            print(f"    [ADS] Seletor aberto via '{abriu}'...")
            time.sleep(2)
            clicou = _mouse_clicar(page, textos_semana)
            if clicou:
                print(f"    [ADS] ✓ Mouse clicou em: '{clicou}'")
                return True

        # Tenta abrir pelo elemento que exibe intervalo de datas (ex: "15/05 - 22/05")
        coord = _clicar_periodo_ads_por_regex(page)
        if coord and isinstance(coord, dict):
            print(f"    [ADS] Abrindo seletor via data '{coord.get('texto', '')}'...")
            page.mouse.move(coord["x"], coord["y"])
            time.sleep(0.3)
            page.mouse.click(coord["x"], coord["y"])
            time.sleep(2)
            clicou = _mouse_clicar(page, textos_semana)
            if clicou:
                print(f"    [ADS] ✓ Mouse clicou em: '{clicou}'")
                return True

        time.sleep(4)

    print("    [ADS] ⚠ Período ADS não selecionado.")
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Extração: Business Insights
# ──────────────────────────────────────────────────────────────────────────────

def _extrair_key_metrics(resp: dict) -> tuple[float, int]:
    """Extrai paid_gmv (BRL) e paid_orders de /api/mydata/v3/dashboard/key-metrics/"""
    if not isinstance(resp, dict):
        return 0.0, 0
    result = resp.get("result") or resp
    if not isinstance(result, dict):
        return 0.0, 0

    fat = 0.0
    gmv = result.get("paid_gmv")
    if isinstance(gmv, dict):
        fat = float(gmv.get("value") or 0)
    elif isinstance(gmv, (int, float)):
        fat = float(gmv)

    ped = 0
    orders = result.get("paid_orders")
    if isinstance(orders, dict):
        ped = int(orders.get("value") or 0)
    elif isinstance(orders, (int, float)):
        ped = int(orders)

    return fat, ped


def _sessao_expirada(page: Page) -> bool:
    try:
        url   = page.url
        texto = page.evaluate("() => document.body.innerText")
        return (
            "buyer/login" in url
            or "accounts.shopee.com.br" in url
            or ("Esqueci minha senha" in texto and "Entrar" in texto)
            or ("ENTRAR" in texto and "Cadastrar" in texto)
        )
    except Exception:
        return False


def _pagina_ativa(context) -> "Page":
    """Retorna a página mais recente do contexto (aba atual após login/redirect)."""
    pages = context.pages
    if not pages:
        return context.new_page()
    # Prefere aba do seller center se existir
    for pg in reversed(pages):
        try:
            if "seller.shopee.com.br" in pg.url:
                return pg
        except Exception:
            pass
    return pages[-1]


def _aguardar_login(page: Page, contexto: str, context=None) -> "Page":
    """
    Se sessão expirou, aguarda até 3 minutos para o usuário logar manualmente.
    Retorna a página atualizada após o login (pode ser diferente da original).
    """
    if not _sessao_expirada(page):
        return page

    _salvar_debug(f"{contexto}_sessao_expirada", {}, page)

    print(f"\n  ⚠  SESSÃO EXPIRADA — {contexto.upper()}")
    print(f"  A página está na tela de login do Shopee.")
    print(f"  Faça login manualmente no Dolphin Anty agora.")
    print(f"  Aguardando até 3 minutos...")
    print()

    logou = False
    for seg in range(180):
        time.sleep(1)
        # Verifica se a página atual ou qualquer aba do contexto já saiu do login
        pg_check = page
        if context:
            try:
                pg_check = _pagina_ativa(context)
            except Exception:
                pass
        if not _sessao_expirada(pg_check):
            print(f"  ✓ Login detectado! Aguardando página estabilizar (10s)...")
            time.sleep(10)
            logou = True
            break
        if seg % 30 == 29:
            print(f"  Aguardando login... {180 - seg - 1}s restantes")

    if not logou:
        raise RuntimeError(
            f"\n\n  ❌  LOGIN NÃO DETECTADO — {contexto.upper()}\n"
            f"  Tempo esgotado (3 minutos). Faça login no Dolphin Anty e rode novamente.\n"
        )

    # Retorna a página ativa atualizada após o login
    if context:
        try:
            return _pagina_ativa(context)
        except Exception:
            pass
    return page


def _checar_sessao_apos_navegacao(page: Page, contexto: str, context=None) -> "Page":
    return _aguardar_login(page, contexto, context)


def coletar_business_insights(page: Page, date_from: datetime, date_to: datetime, context=None) -> dict:
    start_ts = int(date_from.replace(tzinfo=None).timestamp()) if date_from else _timestamps_7_dias()[0]
    end_ts   = int(date_to.replace(tzinfo=None).timestamp())   if date_to   else _timestamps_7_dias()[1]
    print(f"    → Business Insights (período: {datetime.fromtimestamp(start_ts).strftime('%d/%m')} → {datetime.fromtimestamp(end_ts).strftime('%d/%m')})")

    # 1. Navega para a página de Business
    try:
        page.goto(URL_BUSINESS, wait_until="domcontentloaded", timeout=TIMEOUT)
    except Exception:
        pass

    # Aguarda carregamento inicial
    print("    [BUSINESS] Aguardando página carregar (20s)...")
    time.sleep(20)

    # Verifica sessão — aguarda login manual se necessário e retorna página válida
    page = _checar_sessao_apos_navegacao(page, "business", context)

    # Screenshot logo após carregar — para diagnóstico se algo falhar
    _salvar_debug("business_antes", {}, page)

    # 2. Clica em "Últimos 7 Dias" — múltiplas tentativas
    print("    [BUSINESS] Selecionando período 'Últimos 7 Dias'...")
    selecionou = _clicar_7_dias_business(page)

    if selecionou:
        print("    [BUSINESS] Aguardando dados recarregarem (15s)...")
        time.sleep(15)
    else:
        # Se não conseguiu clicar, tira screenshot para diagnóstico
        _salvar_debug("business_sem_periodo", {}, page)
        print("    [BUSINESS] Continuando sem seleção de período — pode retornar dado errado.")
        time.sleep(8)

    fat, ped = 0.0, 0

    # 3. Chamada API com timestamps explícitos (period=custom)
    resp = _fetch_api(page, "/api/mydata/v3/dashboard/key-metrics/", {
        "period":     "custom",
        "start_time": start_ts,
        "end_time":   end_ts,
    })
    _salvar_debug("business", resp, page)

    if resp.get("code") == 0:
        fat, ped = _extrair_key_metrics(resp)
        if fat > 0:
            print(f"    [BUSINESS] ✓ API custom timestamps → R${fat:,.2f} | {ped} pedidos")

    # 4. Fallback: sem period, só timestamps
    if fat == 0.0:
        print("    [BUSINESS] Fallback sem 'period'...")
        resp2 = _fetch_api(page, "/api/mydata/v3/dashboard/key-metrics/", {
            "start_time": start_ts,
            "end_time":   end_ts,
        })
        _salvar_debug("business_ts", resp2)
        if resp2.get("code") == 0:
            fat, ped = _extrair_key_metrics(resp2)
            if fat > 0:
                print(f"    [BUSINESS] ✓ Fallback timestamps → R${fat:,.2f} | {ped} pedidos")

    # 5. Último recurso: ler números do DOM
    if fat == 0.0:
        print("    [BUSINESS] Lendo valores do DOM...")
        fat, ped = _extrair_do_dom_business(page)
        if fat > 0:
            print(f"    [BUSINESS] ✓ DOM → R${fat:,.2f} | {ped} pedidos")

    if fat == 0.0:
        print("    [BUSINESS] ⚠ Faturamento não encontrado! Verifique debug_business_antes.png")

    print(f"    [BUSINESS] Resultado: faturamento=R${fat:,.2f}  pedidos={ped}")

    # ── Semana anterior (via API com timestamps — não precisa clicar na UI) ──
    prev_start, prev_end = _timestamps_semana_anterior()
    print(f"    [BUSINESS] Coletando semana anterior ({datetime.fromtimestamp(prev_start).strftime('%d/%m')} → {datetime.fromtimestamp(prev_end).strftime('%d/%m')})...")
    resp_prev = _fetch_api(page, "/api/mydata/v3/dashboard/key-metrics/", {
        "period":     "custom",
        "start_time": prev_start,
        "end_time":   prev_end,
    })
    fat_prev, ped_prev = _extrair_key_metrics(resp_prev)
    if fat_prev == 0.0:
        # tenta sem period=custom
        resp_prev2 = _fetch_api(page, "/api/mydata/v3/dashboard/key-metrics/", {
            "start_time": prev_start,
            "end_time":   prev_end,
        })
        fat_prev, ped_prev = _extrair_key_metrics(resp_prev2)
    print(f"    [BUSINESS] Semana anterior: R${fat_prev:,.2f} | {ped_prev} pedidos")

    return {
        "faturamento":       fat,
        "total_pedidos":     ped,
        "faturamento_prev":  fat_prev,
        "pedidos_prev":      ped_prev,
    }


def _extrair_do_dom_business(page: Page) -> tuple[float, int]:
    """
    Lê faturamento e pedidos das linhas visíveis na página Business Insights.
    Estratégia: label "Vendas" → próximo valor R$X.XXX,XX; label "Pedidos" → próximo inteiro.
    """
    try:
        texto_pagina = page.evaluate("() => document.body.innerText")
        linhas = [l.strip() for l in texto_pagina.split("\n") if l.strip()]

        fat = 0.0
        ped = 0

        for i, linha in enumerate(linhas):
            # Faturamento: label "Vendas" seguido de R$X.XXX,XX
            if fat == 0.0 and linha.lower() in ("vendas", "total de vendas"):
                for j in range(i + 1, min(i + 4, len(linhas))):
                    m = re.match(r"R?\$\s*([\d\.]+,\d{2})", linhas[j])
                    if m:
                        fat = float(m.group(1).replace(".", "").replace(",", "."))
                        break

            # Pedidos: label "Pedidos" seguido de inteiro
            if ped == 0 and re.fullmatch(r"[Pp]edidos?", linha):
                for j in range(i + 1, min(i + 4, len(linhas))):
                    if re.fullmatch(r"\d+", linhas[j]):
                        ped = int(linhas[j])
                        break

            if fat > 0 and ped > 0:
                break

        return fat, ped
    except Exception:
        return 0.0, 0


def _extrair_do_dom_ads(page: Page) -> dict:
    """
    Lê métricas ADS da seção de resumo da página (Investimento, ROAS, Pedidos).
    Receita = Investimento × ROAS (evita imprecisão de valores abreviados como R$6k).
    """
    try:
        texto_pagina = page.evaluate("() => document.body.innerText")
        linhas = [l.strip() for l in texto_pagina.split("\n") if l.strip()]

        inv = roas = 0.0
        ped = cli = imp = 0

        def _parse_brl(s: str) -> float:
            s = re.sub(r"[R$\s]", "", s).replace(".", "").replace(",", ".")
            if s.lower().endswith("k"):
                return float(s[:-1]) * 1_000
            return float(s)

        for i, linha in enumerate(linhas):
            prox = linhas[i + 1] if i + 1 < len(linhas) else ""

            if inv == 0.0 and linha == "Investimento":
                try:
                    inv = _parse_brl(prox)
                except Exception:
                    pass

            if roas == 0.0 and linha == "ROAS" and inv > 0:
                try:
                    roas = float(prox.replace(",", "."))
                except Exception:
                    pass

            if ped == 0 and linha == "Pedidos":
                try:
                    ped = int(prox)
                except Exception:
                    pass

            if cli == 0 and linha == "Cliques":
                try:
                    cli = int(float(prox.replace("k", "e3").replace(".", "").replace(",", ".")))
                except Exception:
                    pass

            if imp == 0 and linha == "Impressões":
                try:
                    imp = int(float(prox.replace("k", "e3").replace(".", "").replace(",", ".")))
                except Exception:
                    pass

            if inv > 0 and roas > 0 and ped > 0:
                break

        rec = round(inv * roas, 2) if inv > 0 and roas > 0 else 0.0

        return {
            "investimento": round(inv, 2),
            "receita":      rec,
            "roas":         round(roas, 2),
            "pedidos":      ped,
            "cliques":      cli,
            "impressoes":   imp,
        }
    except Exception as e:
        print(f"    [ADS DOM] Erro: {e}")
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# Extração: ADS
# ──────────────────────────────────────────────────────────────────────────────

def _extrair_time_graph(resp: dict) -> dict:
    """
    Extrai de /api/pas/v1/report/get_time_graph/.
    cost e broad_gmv estão em unidades de 1/100.000 de BRL.
    """
    DIVISOR = 100_000
    if not isinstance(resp, dict):
        return {}
    inner = resp.get("data")
    if not isinstance(inner, dict):
        return {}
    report_by_time = inner.get("report_by_time") or []
    if not report_by_time:
        return {}

    total_cost = total_gmv = total_orders = total_clicks = total_impressions = 0
    for item in report_by_time:
        if not isinstance(item, dict):
            continue
        m = item.get("metrics") or {}
        total_cost        += (m.get("cost", 0) or 0)
        total_gmv         += (m.get("broad_gmv", 0) or 0)
        total_orders      += (m.get("broad_order", 0) or 0)
        total_clicks      += (m.get("click", 0) or 0)
        total_impressions += (m.get("impression", 0) or 0)

    inv  = round(total_cost / DIVISOR, 2)
    rec  = round(total_gmv  / DIVISOR, 2)
    roas = round(rec / inv, 2) if inv > 0 else 0.0

    return {
        "investimento": inv,
        "receita":      rec,
        "pedidos":      int(total_orders),
        "cliques":      int(total_clicks),
        "impressoes":   int(total_impressions),
        "roas":         roas,
        "n_slots":      len(report_by_time),
    }


def coletar_ads(page: Page, date_from: datetime, date_to: datetime, context=None) -> dict:
    start_ts = int(date_from.replace(tzinfo=None).timestamp()) if date_from else _timestamps_7_dias()[0]
    end_ts   = int(date_to.replace(tzinfo=None).timestamp())   if date_to   else _timestamps_7_dias()[1]
    print(f"    → ADS (período: {datetime.fromtimestamp(start_ts).strftime('%d/%m')} → {datetime.fromtimestamp(end_ts).strftime('%d/%m')})")

    # 1. Navega para a página de ADS
    try:
        page.goto(URL_ADS, wait_until="domcontentloaded", timeout=TIMEOUT)
    except Exception:
        pass

    print("    [ADS] Aguardando página carregar (20s)...")
    time.sleep(20)

    # Verifica sessão — aguarda login manual se necessário e retorna página válida
    page = _checar_sessao_apos_navegacao(page, "ads", context)

    _salvar_debug("ads_antes", {}, page)

    # 2. Seleciona período "Última semana"
    print("    [ADS] Selecionando período 'Última semana'...")
    _clicar_7_dias_ads(page)
    print("    [ADS] Aguardando dados recarregarem (15s)...")
    time.sleep(15)

    metricas: dict = {}

    # 3. Chamada POST get_time_graph (endpoint exige POST com JSON body)
    resp1 = _post_api(page, "/api/pas/v1/report/get_time_graph/", {
        "start_time":  start_ts,
        "end_time":    end_ts,
        "group_type":  0,
        "report_type": 1,
    })
    _salvar_debug("ads", resp1, page)

    if resp1.get("code") == 0:
        m = _extrair_time_graph(resp1)
        if m.get("n_slots", 0) > 0:
            metricas = m
            print(f"    [ADS] ✓ POST time_graph: {m['n_slots']} slots → inv=R${m['investimento']:,.2f}")

    # 4. Fallback: POST simplificado sem group_type/report_type
    if not metricas:
        print("    [ADS] Fallback: POST simplificado...")
        resp2 = _post_api(page, "/api/pas/v1/report/get_time_graph/", {
            "start_time": start_ts,
            "end_time":   end_ts,
        })
        _salvar_debug("ads_simples", resp2)
        if resp2.get("code") == 0:
            m = _extrair_time_graph(resp2)
            if m.get("n_slots", 0) > 0:
                metricas = m
                print(f"    [ADS] ✓ Fallback POST → {m['n_slots']} slots")

    # 5. Fallback: GET get_time_graph (compatibilidade)
    if not metricas:
        print("    [ADS] Fallback: GET time_graph...")
        resp3 = _fetch_api(page, "/api/pas/v1/report/get_time_graph/", {
            "start_time":  start_ts,
            "end_time":    end_ts,
            "group_type":  0,
            "report_type": 1,
        })
        _salvar_debug("ads_get", resp3)
        if resp3.get("code") == 0:
            m = _extrair_time_graph(resp3)
            if m.get("n_slots", 0) > 0:
                metricas = m
                print(f"    [ADS] ✓ GET time_graph → {m['n_slots']} slots")

    # 6. Fallback: POST resumo
    if not metricas:
        print("    [ADS] Fallback: POST get_report_summary...")
        resp4 = _post_api(page, "/api/pas/v1/report/get_report_summary/", {
            "start_time": start_ts,
            "end_time":   end_ts,
        })
        _salvar_debug("ads_summary", resp4)
        if resp4.get("code") == 0:
            data = resp4.get("data") or {}
            inv = round((data.get("cost", 0) or 0) / 100_000, 2)
            rec = round((data.get("broad_gmv", 0) or 0) / 100_000, 2)
            if inv > 0 or rec > 0:
                metricas = {
                    "investimento": inv,
                    "receita":      rec,
                    "pedidos":      int(data.get("broad_order", 0) or 0),
                    "cliques":      int(data.get("click", 0) or 0),
                    "impressoes":   int(data.get("impression", 0) or 0),
                    "roas":         round(rec / inv, 2) if inv > 0 else 0.0,
                    "n_slots":      1,
                }
                print(f"    [ADS] ✓ summary → inv=R${inv:,.2f} rec=R${rec:,.2f}")

    # 7. Fallback final: leitura direta do DOM
    if not metricas:
        # Verifica se ainda está no painel de ADS (não em login) antes de ler o DOM
        try:
            url_atual = page.url
            texto_atual = page.evaluate("() => document.body.innerText")
        except Exception:
            url_atual = ""
            texto_atual = ""

        sessao_expirada = (
            "buyer/login" in url_atual
            or ("Esqueci minha senha" in texto_atual and "Entrar" in texto_atual)
        )
        if sessao_expirada:
            _salvar_debug("ads_sessao_expirada", {}, page)
            raise RuntimeError(
                "\n\n  ❌  SESSÃO SHOPEE EXPIRADA durante coleta de ADS!\n"
                "  Todos os fallbacks falharam — a página está na tela de login.\n"
                "  Todos os dados de ADS são inválidos. Faça login e tente novamente.\n"
            )

        print("    [ADS] Fallback DOM — lendo valores da página...")
        metricas_dom = _extrair_do_dom_ads(page)
        if metricas_dom.get("investimento", 0) > 0:
            metricas = metricas_dom
            print(f"    [ADS] ✓ DOM → inv=R${metricas['investimento']:,.2f} roas={metricas['roas']:.2f}x")

    if not metricas:
        print("    [ADS] ⚠ Dados ADS não encontrados. Verifique debug_ads_api.json e debug_ads_texto.txt")

    inv = metricas.get("investimento", 0.0)
    rec = metricas.get("receita",      0.0)
    ros = metricas.get("roas",         0.0)
    ped = metricas.get("pedidos",      0)
    cli = metricas.get("cliques",      0)
    imp = metricas.get("impressoes",   0)

    print(f"    [ADS] inv=R${inv:,.2f}  receita=R${rec:,.2f}  roas={ros:.2f}x  pedidos={ped}")

    # ── Semana anterior ADS ──
    prev_start, prev_end = _timestamps_semana_anterior()
    print(f"    [ADS] Semana anterior ({datetime.fromtimestamp(prev_start).strftime('%d/%m')} → {datetime.fromtimestamp(prev_end).strftime('%d/%m')})...")
    m_prev: dict = {}

    # Tentativa 1: POST com group_type/report_type
    resp_prev = _post_api(page, "/api/pas/v1/report/get_time_graph/", {
        "start_time":  prev_start,
        "end_time":    prev_end,
        "group_type":  0,
        "report_type": 1,
    })
    if resp_prev.get("code") == 0:
        m_prev = _extrair_time_graph(resp_prev)

    # Tentativa 2: POST simplificado
    if not m_prev:
        resp_prev = _post_api(page, "/api/pas/v1/report/get_time_graph/", {
            "start_time": prev_start,
            "end_time":   prev_end,
        })
        if resp_prev.get("code") == 0:
            m_prev = _extrair_time_graph(resp_prev)

    # Tentativa 3: GET
    if not m_prev:
        resp_prev = _fetch_api(page, "/api/pas/v1/report/get_time_graph/", {
            "start_time":  prev_start,
            "end_time":    prev_end,
            "group_type":  0,
            "report_type": 1,
        })
        if resp_prev.get("code") == 0:
            m_prev = _extrair_time_graph(resp_prev)

    # Tentativa 4: summary
    if not m_prev:
        resp_prev = _post_api(page, "/api/pas/v1/report/get_report_summary/", {
            "start_time": prev_start,
            "end_time":   prev_end,
        })
        if resp_prev.get("code") == 0:
            data_prev = resp_prev.get("data") or {}
            inv_p = round((data_prev.get("cost", 0) or 0) / 100_000, 2)
            rec_p = round((data_prev.get("broad_gmv", 0) or 0) / 100_000, 2)
            if inv_p > 0 or rec_p > 0:
                m_prev = {
                    "investimento": inv_p,
                    "receita":      rec_p,
                    "roas":         round(rec_p / inv_p, 2) if inv_p > 0 else 0.0,
                    "pedidos":      int(data_prev.get("broad_order", 0) or 0),
                }

    inv_prev = m_prev.get("investimento", 0.0)
    rec_prev = m_prev.get("receita",      0.0)
    ros_prev = m_prev.get("roas",         0.0)
    print(f"    [ADS] Semana anterior: inv=R${inv_prev:,.2f}  receita=R${rec_prev:,.2f}  roas={ros_prev:.2f}x")

    return {
        "investimento_ads":      round(inv, 2),
        "receita_ads":           round(rec, 2),
        "roas":                  round(ros, 2),
        "quantidade_vendas_ads": ped,
        "cliques":               cli,
        "impressoes":            imp,
        "investimento_ads_prev": round(inv_prev, 2),
        "receita_ads_prev":      round(rec_prev, 2),
        "roas_prev":             round(ros_prev, 2),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Entrada principal
# ──────────────────────────────────────────────────────────────────────────────

def coletar_dados_shopee(page: Page, date_from: datetime, date_to: datetime, context=None) -> dict:
    """Coleta e consolida todos os dados do Shopee Seller Center."""

    # Verificação de sessão — aguarda login manual se necessário
    if not _esta_logado(page) or _sessao_expirada(page):
        try:
            page.goto(URL_BUSINESS, wait_until="domcontentloaded", timeout=TIMEOUT)
        except Exception:
            pass
        time.sleep(5)
        page = _aguardar_login(page, "inicio", context)

    business = coletar_business_insights(page, date_from, date_to, context)

    # Usa a página mais atualizada do contexto para ADS (pode ter mudado após login)
    if context:
        try:
            page = _pagina_ativa(context)
        except Exception:
            pass
    ads = coletar_ads(page, date_from, date_to, context)

    faturamento  = business["faturamento"]
    investimento = ads["investimento_ads"]
    fat_prev     = business.get("faturamento_prev", 0.0)
    inv_prev     = ads.get("investimento_ads_prev", 0.0)
    rec_prev     = ads.get("receita_ads_prev", 0.0)

    tacos      = round(investimento / faturamento * 100, 2) if faturamento > 0 else 0.0
    tacos_prev = round(inv_prev / fat_prev * 100, 2)       if fat_prev > 0     else 0.0

    def _var(atual, anterior):
        """Variação percentual em relação à semana anterior."""
        if anterior == 0:
            return None
        return round((atual - anterior) / anterior * 100, 1)

    start_ts, end_ts         = _timestamps_7_dias()
    prev_start, prev_end     = _timestamps_semana_anterior()
    periodo_de  = datetime.fromtimestamp(start_ts).strftime("%d/%m/%Y")
    periodo_ate = datetime.fromtimestamp(end_ts).strftime("%d/%m/%Y")
    prev_de     = datetime.fromtimestamp(prev_start).strftime("%d/%m/%Y")
    prev_ate    = datetime.fromtimestamp(prev_end).strftime("%d/%m/%Y")

    return {
        "periodo": {"de": periodo_de, "ate": periodo_ate},
        "periodo_anterior": {"de": prev_de, "ate": prev_ate},
        # Semana atual
        "faturamento":           faturamento,
        "total_pedidos":         business["total_pedidos"],
        "investimento_ads":      investimento,
        "receita_ads":           ads["receita_ads"],
        "roas":                  ads["roas"],
        "tacos":                 tacos,
        "quantidade_vendas_ads": ads["quantidade_vendas_ads"],
        "cliques":               ads.get("cliques", 0),
        "impressoes":            ads.get("impressoes", 0),
        # Semana anterior
        "faturamento_prev":      fat_prev,
        "pedidos_prev":          business.get("pedidos_prev", 0),
        "investimento_ads_prev": inv_prev,
        "receita_ads_prev":      rec_prev,
        "roas_prev":             ads.get("roas_prev", 0.0),
        "tacos_prev":            tacos_prev,
        # Variações percentuais
        "var_faturamento":       _var(faturamento, fat_prev),
        "var_pedidos":           _var(business["total_pedidos"], business.get("pedidos_prev", 0)),
        "var_investimento":      _var(investimento, inv_prev),
        "var_receita_ads":       _var(ads["receita_ads"], rec_prev),
        "var_roas":              _var(ads["roas"], ads.get("roas_prev", 0.0)),
        "var_tacos":             _var(tacos, tacos_prev),
    }
