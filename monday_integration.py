"""
Integração com Monday.com para envio automático do relatório semanal Shopee.
Para cada cliente: garante que o grupo existe, cria item e adiciona update com métricas.
"""

import requests
import config


MONDAY_API_URL  = "https://api.monday.com/v2"
MONDAY_BOARD_ID = config.MONDAY_BOARD_ID

HEADERS = {
    "Authorization": config.MONDAY_API_TOKEN,
    "Content-Type":  "application/json",
    "API-Version":   "2023-10",
}


def _gql(query: str, variables: dict = None, _tentativa: int = 1) -> dict:
    import time
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(MONDAY_API_URL, json=payload, headers=HEADERS, timeout=30)
    if resp.status_code == 429 and _tentativa <= 3:
        espera = 60 * _tentativa
        print(f"[Monday] Rate limit (429) — aguardando {espera}s (tentativa {_tentativa}/3)...")
        time.sleep(espera)
        return _gql(query, variables, _tentativa + 1)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Erro Monday API: {data['errors']}")
    return data


def _listar_grupos() -> list[dict]:
    """Retorna lista de grupos do board: [{id, title}, ...]"""
    query = """
    query ($board_id: ID!) {
      boards(ids: [$board_id]) {
        groups { id title }
      }
    }
    """
    result = _gql(query, {"board_id": MONDAY_BOARD_ID})
    return result["data"]["boards"][0]["groups"]


def _criar_grupo(nome_cliente: str) -> str:
    """Cria um novo grupo no board e retorna seu ID."""
    query = """
    mutation ($board_id: ID!, $group_name: String!) {
      create_group(board_id: $board_id, group_name: $group_name) {
        id
      }
    }
    """
    result = _gql(query, {"board_id": MONDAY_BOARD_ID, "group_name": nome_cliente})
    group_id = result["data"]["create_group"]["id"]
    print(f"[Monday] Grupo criado: '{nome_cliente}' (ID: {group_id})")
    return group_id


def _obter_ou_criar_grupo(nome_cliente: str) -> str:
    """Retorna o ID do grupo do cliente, criando-o se não existir."""
    grupos = _listar_grupos()
    nome_lower = nome_cliente.lower().strip()
    for grupo in grupos:
        if grupo["title"].lower().strip() == nome_lower:
            return grupo["id"]
    return _criar_grupo(nome_cliente)


def _fmt_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _criar_item(group_id: str, nome_item: str) -> str:
    query = """
    mutation ($board_id: ID!, $group_id: String!, $item_name: String!) {
      create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name) {
        id
      }
    }
    """
    variables = {
        "board_id":  MONDAY_BOARD_ID,
        "group_id":  group_id,
        "item_name": nome_item,
    }
    result = _gql(query, variables)
    item_id = result["data"]["create_item"]["id"]
    print(f"[Monday] Item criado: '{nome_item}' (ID: {item_id})")
    return item_id


def _seta(var) -> str:
    if var is None: return "—"
    if var > 0:  return f"▲ {var:.1f}%"
    if var < 0:  return f"▼ {abs(var):.1f}%"
    return "→ 0,0%"


def _adicionar_update(item_id: str, dados: dict, nome_cliente: str) -> None:
    periodo  = dados["periodo"]
    prev     = dados.get("periodo_anterior", {"de": "—", "ate": "—"})
    fat      = dados["faturamento"]
    inv      = dados["investimento_ads"]
    qtd_ads  = dados.get("quantidade_vendas_ads", 0)
    tacos    = dados["tacos"]
    roas     = dados["roas"]
    rec_ads  = dados["receita_ads"]
    pedidos  = dados["total_pedidos"]

    fat_prev  = dados.get("faturamento_prev", 0.0)
    ped_prev  = dados.get("pedidos_prev", 0)
    inv_prev  = dados.get("investimento_ads_prev", 0.0)
    rec_prev  = dados.get("receita_ads_prev", 0.0)
    roas_prev = dados.get("roas_prev", 0.0)
    tacos_prev= dados.get("tacos_prev", 0.0)

    corpo = (
        f"📊 RELATÓRIO SEMANAL SHOPEE — {nome_cliente}\n"
        f"Período: {periodo['de']} → {periodo['ate']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Faturamento Bruto: {_fmt_brl(fat)}\n"
        f"🛒 Total de Pedidos: {pedidos}\n\n"
        f"📢 PRODUCT ADS\n"
        f"  • Investimento: {_fmt_brl(inv)}\n"
        f"  • Receita via ADS: {_fmt_brl(rec_ads)}\n"
        f"  • Qtd. Vendas (ADS): {qtd_ads}\n\n"
        f"📈 MÉTRICAS DE EFICIÊNCIA\n"
        f"  • TACOS: {tacos:.2f}%\n"
        f"  • ROAS: {roas:.2f}x\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 COMPARATIVO — Semana anterior ({prev['de']} → {prev['ate']})\n\n"
        f"  Métrica           | Atual              | Anterior           | Var.\n"
        f"  Faturamento       | {_fmt_brl(fat):<18} | {_fmt_brl(fat_prev):<18} | {_seta(dados.get('var_faturamento'))}\n"
        f"  Pedidos           | {pedidos:<18} | {ped_prev:<18} | {_seta(dados.get('var_pedidos'))}\n"
        f"  Invest. ADS       | {_fmt_brl(inv):<18} | {_fmt_brl(inv_prev):<18} | {_seta(dados.get('var_investimento'))}\n"
        f"  Receita ADS       | {_fmt_brl(rec_ads):<18} | {_fmt_brl(rec_prev):<18} | {_seta(dados.get('var_receita_ads'))}\n"
        f"  ROAS              | {roas:.2f}x{'':<14} | {roas_prev:.2f}x{'':<14} | {_seta(dados.get('var_roas'))}\n"
        f"  TACOS             | {tacos:.2f}%{'':<14} | {tacos_prev:.2f}%{'':<14} | {_seta(dados.get('var_tacos'))}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Gerado automaticamente via Shopee Open Platform API."
    )

    query = """
    mutation ($item_id: ID!, $body: String!) {
      create_update(item_id: $item_id, body: $body) {
        id
      }
    }
    """
    _gql(query, {"item_id": item_id, "body": corpo})
    print("[Monday] Update com métricas adicionado.")


def enviar_relatorio_monday(dados: dict, nome_cliente: str) -> None:
    """
    Garante que o grupo do cliente existe, cria o item do relatório
    e adiciona update com todas as métricas.
    """
    print(f"\n── MONDAY.COM → {nome_cliente} ────────────────────────")
    try:
        periodo   = dados["periodo"]
        group_id  = _obter_ou_criar_grupo(nome_cliente)
        nome_item = f"Relatório Semanal | {periodo['de']} → {periodo['ate']}"
        item_id   = _criar_item(group_id, nome_item)
        _adicionar_update(item_id, dados, nome_cliente)
        print(f"  ✓ Relatório enviado com sucesso para o grupo '{nome_cliente}'.")
    except Exception as e:
        print(f"  ✗ Falha ao enviar para Monday.com: {e}")
    print("────────────────────────────────────────────────────\n")
