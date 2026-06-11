# -*- coding: utf-8 -*-
"""Teste rapido das correcoes aplicadas ao shopee_scraper.py"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ── Mock da Page do Playwright ───────────────────────────────────────────────
class MockPage:
    def __init__(self, url, innertext):
        self.url = url
        self._text = innertext

    def evaluate(self, expr):
        return self._text

    def screenshot(self, **kw):
        pass


import shopee_scraper as sc

ok = 0
falhou = 0


def check(nome, passou, detalhe=""):
    global ok, falhou
    if passou:
        ok += 1
        print(f"  PASSOU ✓  {nome}")
        if detalhe:
            print(f"            {detalhe}")
    else:
        falhou += 1
        print(f"  FALHOU ✗  {nome}")
        if detalhe:
            print(f"            {detalhe}")


print("=" * 60)
print("  shopee_scraper — testes das correções de sessão/ADS")
print("=" * 60)

# ── Teste 1: RuntimeError em URL de login ────────────────────
try:
    sc._checar_sessao_apos_navegacao(
        MockPage("https://seller.shopee.com.br/buyer/login?from=/portal/marketing/pas/index",
                 "Esqueci minha senha\nEntrar\nCadastrar"),
        "ads"
    )
    check("1 — URL de login levanta RuntimeError", False, "deveria ter lançado RuntimeError")
except RuntimeError as e:
    check("1 — URL de login levanta RuntimeError", True, str(e).split("\n")[1].strip())

# ── Teste 2: RuntimeError por texto da página ────────────────
try:
    sc._checar_sessao_apos_navegacao(
        MockPage("https://seller.shopee.com.br/portal/marketing/pas/index",
                 "Esqueci minha senha\nEntrar\nCadastrar\nNovo na Shopee?"),
        "ads"
    )
    check("2 — Texto de login levanta RuntimeError", False)
except RuntimeError:
    check("2 — Texto de login levanta RuntimeError", True)

# ── Teste 3: Sessão válida NÃO levanta exceção ───────────────
try:
    sc._checar_sessao_apos_navegacao(
        MockPage("https://seller.shopee.com.br/portal/marketing/pas/index",
                 "Resumo de performance\nInvestimento\nROAS\nPedidos"),
        "ads"
    )
    check("3 — Sessão válida não lança exceção", True)
except RuntimeError as e:
    check("3 — Sessão válida não lança exceção", False, str(e))

# ── Teste 4: _esta_logado → False em login ───────────────────
resultado = sc._esta_logado(
    MockPage("https://seller.shopee.com.br/buyer/login",
             "Esqueci minha senha\nEntrar\nCadastrar")
)
check("4 — _esta_logado retorna False na tela de login", resultado is False)

# ── Teste 5: _esta_logado → True em painel válido ────────────
resultado = sc._esta_logado(
    MockPage("https://seller.shopee.com.br/datacenter/overview",
             "Resumo de vendas\nPedidos pagos\nFaturamento")
)
check("5 — _esta_logado retorna True no painel válido", resultado is True)

# ── Teste 6: _extrair_time_graph com 2 slots ─────────────────
DIVISOR = 100_000
resp = {
    "code": 0,
    "data": {
        "report_by_time": [
            {"metrics": {"cost": 1_500_000_000, "broad_gmv": 9_000_000_000, "broad_order": 42, "click": 300, "impression": 5000}},
            {"metrics": {"cost":   500_000_000, "broad_gmv": 3_000_000_000, "broad_order": 14, "click": 100, "impression": 2000}},
        ]
    }
}
m = sc._extrair_time_graph(resp)
inv_exp  = round(2_000_000_000 / DIVISOR, 2)   # 20000.00
rec_exp  = round(12_000_000_000 / DIVISOR, 2)  # 120000.00
roas_exp = round(rec_exp / inv_exp, 2)          # 6.0
passou = (
    m.get("investimento") == inv_exp
    and m.get("receita") == rec_exp
    and m.get("roas") == roas_exp
    and m.get("pedidos") == 56
    and m.get("n_slots") == 2
)
check("6 — _extrair_time_graph calcula valores corretos",
      passou,
      f"inv=R${m.get('investimento'):,.2f}  rec=R${m.get('receita'):,.2f}  roas={m.get('roas')}x  pedidos={m.get('pedidos')}")

# ── Teste 7: _extrair_time_graph com resposta vazia ──────────
m_vazio = sc._extrair_time_graph({"code": 0, "data": {"report_by_time": []}})
check("7 — _extrair_time_graph retorna {} para lista vazia", m_vazio == {})

# ── Teste 8: _extrair_time_graph com resposta de erro ────────
m_erro = sc._extrair_time_graph({"_fetch_error": "TypeError: Failed to fetch"})
check("8 — _extrair_time_graph retorna {} para _fetch_error", m_erro == {})

# ── Teste 9: ROAS = 0 quando investimento é 0 ────────────────
resp_zero = {
    "code": 0,
    "data": {
        "report_by_time": [
            {"metrics": {"cost": 0, "broad_gmv": 5_000_000_000, "broad_order": 10, "click": 0, "impression": 0}},
        ]
    }
}
m_zero = sc._extrair_time_graph(resp_zero)
check("9 — ROAS = 0.0 quando investimento é zero (sem divisão por zero)", m_zero.get("roas") == 0.0,
      f"roas={m_zero.get('roas')}")

# ── Resultado ────────────────────────────────────────────────
print()
print("=" * 60)
print(f"  Resultado: {ok} passou  |  {falhou} falhou")
print("=" * 60)
sys.exit(0 if falhou == 0 else 1)
