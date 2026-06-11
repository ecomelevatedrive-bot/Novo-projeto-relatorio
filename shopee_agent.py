"""
Agente de extração de dados da Shopee via Open Platform API.
Coleta: pedidos pagos, faturamento, dados de ADS (investimento, receita, ROAS, ACOS).
"""

import hashlib
import hmac
import time
import requests
from datetime import datetime, timezone
from typing import Optional

import config


# ──────────────────────────────────────────────
#  AUTENTICAÇÃO
# ──────────────────────────────────────────────

def _sign(path: str, timestamp: int) -> str:
    """Gera assinatura HMAC-SHA256 exigida pela Shopee API."""
    base_string = f"{config.PARTNER_ID}{path}{timestamp}{config.ACCESS_TOKEN}{config.SHOP_ID}"
    return hmac.new(
        config.PARTNER_KEY.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _build_url(path: str) -> tuple[str, dict]:
    """Retorna URL completa e parâmetros de autenticação base."""
    ts = int(time.time())
    return (
        f"{config.BASE_URL}{path}",
        {
            "partner_id":   config.PARTNER_ID,
            "shop_id":      config.SHOP_ID,
            "access_token": config.ACCESS_TOKEN,
            "timestamp":    ts,
            "sign":         _sign(path, ts),
        },
    )


def _get(path: str, extra_params: Optional[dict] = None) -> dict:
    url, params = _build_url(path)
    if extra_params:
        params.update(extra_params)
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"Erro Shopee API [{path}]: {data.get('message')} — {data.get('error')}")
    return data


# ──────────────────────────────────────────────
#  EXTRAÇÃO: PEDIDOS PAGOS / FATURAMENTO
# ──────────────────────────────────────────────

def get_pedidos_pagos(date_from: datetime, date_to: datetime) -> dict:
    """
    Busca todos os pedidos com status PAID/COMPLETED no período.
    Retorna: { total_pedidos, faturamento_bruto }
    """
    ts_from = int(date_from.replace(tzinfo=timezone.utc).timestamp())
    ts_to   = int(date_to.replace(tzinfo=timezone.utc).timestamp())

    pedidos = []
    cursor  = ""

    while True:
        params = {
            "time_range_field": "create_time",
            "time_from":        ts_from,
            "time_to":          ts_to,
            "page_size":        100,
            "order_status":     "PAID",
        }
        if cursor:
            params["cursor"] = cursor

        data   = _get("/api/v2/order/get_order_list", params)
        items  = data.get("response", {}).get("order_list", [])
        pedidos.extend(items)

        more   = data.get("response", {}).get("more", False)
        cursor = data.get("response", {}).get("next_cursor", "")
        if not more:
            break

    # Busca detalhes de cada pedido para somar o total_amount
    faturamento = 0.0
    order_sns   = [p["order_sn"] for p in pedidos]

    # A API aceita até 50 order_sn por chamada
    for i in range(0, len(order_sns), 50):
        chunk = order_sns[i : i + 50]
        detail_data = _get(
            "/api/v2/order/get_order_detail",
            {
                "order_sn_list":   ",".join(chunk),
                "response_optional_fields": "total_amount,order_status,payment_method",
            },
        )
        for order in detail_data.get("response", {}).get("order_list", []):
            faturamento += float(order.get("total_amount", 0))

    return {
        "total_pedidos":   len(pedidos),
        "faturamento":     round(faturamento, 2),
    }


# ──────────────────────────────────────────────
#  EXTRAÇÃO: DADOS DE ADS
# ──────────────────────────────────────────────

def get_dados_ads(date_from: datetime, date_to: datetime) -> dict:
    """
    Busca relatório agregado de ADS no período.
    Retorna: { investimento_ads, receita_ads, roas, acos }
    """
    data = _get(
        "/api/v2/ads/get_shop_report",
        {
            "start_date": date_from.strftime("%Y-%m-%d"),
            "end_date":   date_to.strftime("%Y-%m-%d"),
            "granularity": "TOTAL",
            "fields": "expense,gmv,roas,acos,impression,click,order",
        },
    )

    report = data.get("response", {}).get("report_list", [{}])[0] if data.get("response", {}).get("report_list") else {}

    investimento      = float(report.get("expense", 0))
    receita_ads       = float(report.get("gmv", 0))
    roas              = float(report.get("roas", 0))
    acos              = float(report.get("acos", 0))
    qtd_vendas_ads    = int(report.get("order", 0))

    return {
        "investimento_ads":   round(investimento, 2),
        "receita_ads":        round(receita_ads, 2),
        "roas":               round(roas, 4),
        "acos":               round(acos * 100, 2),
        "quantidade_vendas_ads": qtd_vendas_ads,
    }


# ──────────────────────────────────────────────
#  AGENTE PRINCIPAL
# ──────────────────────────────────────────────

class ShopeeAgent:
    """
    Agente responsável por coletar e consolidar todos os dados
    de performance da loja Shopee para o período informado.
    """

    def __init__(self, date_from: datetime, date_to: datetime):
        self.date_from = date_from
        self.date_to   = date_to

    def coletar(self) -> dict:
        print(f"[Agente] Coletando dados de {self.date_from.date()} até {self.date_to.date()}...")

        print("  → Buscando pedidos pagos...")
        pedidos = get_pedidos_pagos(self.date_from, self.date_to)

        print("  → Buscando dados de ADS...")
        ads = get_dados_ads(self.date_from, self.date_to)

        faturamento = pedidos["faturamento"]
        investimento = ads["investimento_ads"]

        # TACOS = (Investimento ADS / Faturamento Total) × 100
        tacos = round((investimento / faturamento * 100), 2) if faturamento > 0 else 0.0

        resultado = {
            "periodo": {
                "de":  self.date_from.strftime("%d/%m/%Y"),
                "ate": self.date_to.strftime("%d/%m/%Y"),
            },
            "faturamento":         faturamento,
            "total_pedidos":       pedidos["total_pedidos"],
            "investimento_ads":    investimento,
            "receita_ads":         ads["receita_ads"],
            "roas":                ads["roas"],
            "acos":                ads["acos"],
            "tacos":               tacos,
            "quantidade_vendas_ads": ads["quantidade_vendas_ads"],
        }

        print("  ✓ Coleta concluída.")
        return resultado
