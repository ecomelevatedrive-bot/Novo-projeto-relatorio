"""
Automação de relatórios Shopee + Monday.com via Dolphin Anty.

Uso:
  python main.py                        # todos os perfis com tag Shopee, últimos 7 dias
  python main.py 2025-04-01 2025-04-30  # período personalizado
  python main.py --cliente "TM Santos"  # somente um cliente específico
"""

import os
import sys
import time
from datetime import datetime, date, timedelta

import config
from dolphin_browser import listar_perfis_shopee, iniciar_perfil, parar_perfil
from shopee_scraper import coletar_dados_shopee
from report_generator import gerar_relatorio
from monday_integration import enviar_relatorio_monday


def _parse_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        print(f"[Erro] Data inválida '{s}'. Use o formato AAAA-MM-DD.")
        sys.exit(1)


def _periodo_ultimos_7_dias() -> tuple[datetime, datetime]:
    ontem  = date.today() - timedelta(days=1)
    inicio = ontem - timedelta(days=6)
    fim    = datetime(ontem.year, ontem.month, ontem.day, 23, 59, 59)
    inicio = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)
    return inicio, fim


def _parse_args():
    args           = sys.argv[1:]
    filtro_cliente = None
    datas          = []
    i = 0
    while i < len(args):
        if args[i] == "--cliente" and i + 1 < len(args):
            filtro_cliente = args[i + 1]
            i += 2
        else:
            datas.append(args[i])
            i += 1

    if len(datas) == 2:
        date_from = _parse_date(datas[0])
        date_to   = _parse_date(datas[1])
    elif len(datas) == 0:
        date_from, date_to = _periodo_ultimos_7_dias()
    else:
        print("Uso: python main.py [AAAA-MM-DD AAAA-MM-DD] [--cliente NOME]")
        sys.exit(1)

    return date_from, date_to, filtro_cliente


def processar_cliente(perfil: dict, date_from: datetime, date_to: datetime) -> None:
    nome       = perfil["nome"]
    profile_id = perfil["id"]

    print()
    print("=" * 55)
    print(f"  CLIENTE : {nome}")
    print(f"  Período : {date_from.strftime('%d/%m/%Y')} → {date_to.strftime('%d/%m/%Y')}")
    print("=" * 55)

    print(f"  Iniciando perfil Dolphin (ID: {profile_id})...")
    ws_endpoint = iniciar_perfil(profile_id)
    print(f"  Conectado: {ws_endpoint}")
    time.sleep(3)

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            # Tenta reutilizar aba já logada; senão abre nova
            page = None
            for pg in context.pages:
                try:
                    if "seller.shopee.com.br" in pg.url:
                        page = pg
                        print(f"  Reutilizando aba: {pg.url[:60]}")
                        break
                except Exception:
                    pass
            if page is None:
                # Nenhuma aba do seller center — pega qualquer aba disponível
                if context.pages:
                    page = context.pages[0]
                else:
                    page = context.new_page()

            dados = coletar_dados_shopee(page, date_from, date_to, context)

            # Após coletar, atualiza referência caso a aba tenha mudado
            try:
                _ = page.url
            except Exception:
                # page ficou inválida — pega a aba atual do contexto
                page = context.pages[0] if context.pages else page

            try:
                page.close()
            except Exception:
                pass
            browser.close()

    finally:
        print(f"  Parando perfil {profile_id}...")
        parar_perfil(profile_id)
        time.sleep(2)

    def _seta(var):
        if var is None: return "   —   "
        if var > 0:  return f"▲{var:+.1f}%"
        if var < 0:  return f"▼{var:.1f}%"
        return " →0,0%"

    prev = dados.get("periodo_anterior", {})
    print("\n── SEMANA ATUAL ─────────────────────────────────────")
    print(f"  Faturamento Bruto           : R$ {dados['faturamento']:>12,.2f}")
    print(f"  Total de Pedidos            : {dados['total_pedidos']:>13}")
    print(f"  Investimento ADS            : R$ {dados['investimento_ads']:>12,.2f}")
    print(f"  Receita via ADS             : R$ {dados['receita_ads']:>12,.2f}")
    print(f"  Qtd. Vendas (ADS)           : {dados.get('quantidade_vendas_ads', 0):>13}")
    print(f"  ROAS                        : {dados['roas']:>14.2f}x")
    print(f"  TACOS                       : {dados['tacos']:>13.2f}%")
    print(f"\n── COMPARATIVO ({prev.get('de','—')} → {prev.get('ate','—')}) ──────────")
    print(f"  {'Métrica':<28} {'Anterior':>12}   {'Variação'}")
    print(f"  {'─'*55}")
    print(f"  {'Faturamento':<28} R${dados.get('faturamento_prev',0):>10,.2f}   {_seta(dados.get('var_faturamento'))}")
    print(f"  {'Pedidos':<28} {dados.get('pedidos_prev',0):>12}   {_seta(dados.get('var_pedidos'))}")
    print(f"  {'Investimento ADS':<28} R${dados.get('investimento_ads_prev',0):>10,.2f}   {_seta(dados.get('var_investimento'))}")
    print(f"  {'Receita ADS':<28} R${dados.get('receita_ads_prev',0):>10,.2f}   {_seta(dados.get('var_receita_ads'))}")
    print(f"  {'ROAS':<28} {dados.get('roas_prev',0):>11.2f}x   {_seta(dados.get('var_roas'))}")
    print(f"  {'TACOS':<28} {dados.get('tacos_prev',0):>11.2f}%   {_seta(dados.get('var_tacos'))}")
    print("────────────────────────────────────────────────────")

    dados["nome_cliente"] = nome
    gerar_relatorio(dados, output_dir=f"reports/{nome.replace(' ', '_')}")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop", nome.replace(" ", "_"))
    gerar_relatorio(dados, output_dir=desktop)
    enviar_relatorio_monday(dados, nome)


def main():
    date_from, date_to, filtro_cliente = _parse_args()

    if date_from > date_to:
        print("[Erro] A data inicial deve ser anterior à data final.")
        sys.exit(1)

    print()
    print("=" * 55)
    print("  AUTOMAÇÃO DE RELATÓRIOS — SHOPEE + MONDAY.COM")
    print("=" * 55)
    print(f"  Período : {date_from.strftime('%d/%m/%Y')} → {date_to.strftime('%d/%m/%Y')}")
    print(f"  Fonte   : Dolphin Anty (tag: Shopee)")
    print("=" * 55)

    print("\n[Dolphin] Buscando perfis com tag 'Shopee'...")
    perfis = listar_perfis_shopee()

    if filtro_cliente:
        perfis = [p for p in perfis if p["nome"].lower() == filtro_cliente.lower()]

    if not perfis:
        print("\n[Aviso] Nenhum perfil encontrado com a tag 'Shopee'.")
        print("Adicione a tag 'Shopee' nos perfis corretos dentro do Dolphin Anty.")
        sys.exit(0)

    print(f"  {len(perfis)} perfil(is) encontrado(s): {', '.join(p['nome'] for p in perfis)}\n")

    erros = []
    for perfil in perfis:
        try:
            processar_cliente(perfil, date_from, date_to)
        except Exception as e:
            print(f"\n[Erro] Falha ao processar '{perfil['nome']}': {e}")
            erros.append(perfil["nome"])
            parar_perfil(perfil["id"])

    print()
    print("=" * 55)
    print(f"  Automação concluída!")
    print(f"  Sucesso: {len(perfis) - len(erros)} | Erros: {len(erros)}")
    if erros:
        print(f"  Com erro: {', '.join(erros)}")
    print("=" * 55)


if __name__ == "__main__":
    main()
