"""
Gerador do Dashboard HTML de Performance Shopee.
Design baseado em relatorio_foreli_abril2026.html (Elevate Ecom — Team Jaguar).
"""

import os
from datetime import datetime


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório Shopee — {nome_cliente} — {de} a {ate}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --navy-900: #060E1C;
    --navy-800: #0B1629;
    --navy-700: #0F2040;
    --navy-600: #152B52;
    --navy-500: #1E3A6A;
    --card-bg:  #0E1D35;
    --card-border: rgba(99,179,237,0.14);
    --accent:   #63B3ED;
    --accent2:  #90CDF4;
    --green:    #48BB78;
    --yellow:   #ECC94B;
    --red:      #FC8181;
    --text:     #E2E8F0;
    --text-muted: rgba(226,232,240,0.45);
  }}

  body {{
    font-family: 'Poppins', sans-serif;
    background: var(--navy-800);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── TOPBAR (logo Elevate Ecom) ── */
  .topbar {{
    background: var(--navy-900);
    border-bottom: 1px solid rgba(99,179,237,0.12);
    padding: 14px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .topbar-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .topbar-icon {{
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), #4299E1);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 900; color: #fff;
    letter-spacing: -1px;
  }}
  .topbar-name {{
    font-size: 15px; font-weight: 800;
    color: #fff; letter-spacing: -0.3px;
  }}
  .topbar-name span {{ color: var(--accent); }}
  .topbar-tag {{
    font-size: 10px; font-weight: 600;
    color: var(--text-muted); letter-spacing: 2px;
    text-transform: uppercase;
  }}

  /* ── HERO ── */
  .hero {{
    background:
      radial-gradient(ellipse at 80% 20%, rgba(99,179,237,0.12) 0%, transparent 55%),
      radial-gradient(ellipse at 10% 80%, rgba(66,153,225,0.08) 0%, transparent 50%),
      linear-gradient(160deg, var(--navy-700) 0%, var(--navy-800) 50%, var(--navy-900) 100%);
    padding: 64px 40px 56px;
    text-align: center;
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid rgba(99,179,237,0.1);
  }}
  .hero::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.4;
  }}

  .hero-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(99,179,237,0.08);
    border: 1px solid rgba(99,179,237,0.25);
    color: var(--accent);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 22px;
  }}
  .hero-eyebrow::before {{
    content: '';
    width: 6px; height: 6px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50%       {{ opacity: 0.5; transform: scale(0.8); }}
  }}

  .hero-client {{
    font-size: clamp(14px, 2vw, 17px);
    font-weight: 600;
    color: var(--accent2);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}

  .hero h1 {{
    font-size: clamp(34px, 5.5vw, 60px);
    font-weight: 900;
    color: #fff;
    letter-spacing: -2px;
    line-height: 1.05;
    margin-bottom: 14px;
  }}
  .hero h1 em {{
    font-style: normal;
    background: linear-gradient(90deg, var(--accent), #90CDF4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}

  .hero-period {{
    display: inline-block;
    font-size: 13px;
    color: var(--text-muted);
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    padding: 6px 18px;
    border-radius: 20px;
    margin-bottom: 44px;
  }}

  .hero-kpis {{
    display: flex;
    justify-content: center;
    gap: 0;
    flex-wrap: wrap;
    max-width: 860px;
    margin: 0 auto;
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 18px;
    overflow: hidden;
    background: rgba(6,14,28,0.6);
    backdrop-filter: blur(10px);
  }}
  .hero-kpi {{
    flex: 1;
    min-width: 140px;
    padding: 22px 20px;
    text-align: center;
    border-right: 1px solid rgba(99,179,237,0.1);
    position: relative;
  }}
  .hero-kpi:last-child {{ border-right: none; }}
  .hero-kpi-label {{
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
  }}
  .hero-kpi-value {{
    font-size: clamp(18px, 2.5vw, 24px);
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
  }}

  /* ── LAYOUT ── */
  .container {{ max-width: 1120px; margin: 0 auto; padding: 0 28px; }}
  .section {{ padding: 56px 0; }}
  .section-label {{
    font-size: 11px; font-weight: 700;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--accent); margin-bottom: 6px;
  }}
  .section-heading {{
    font-size: clamp(20px, 2.8vw, 28px);
    font-weight: 700; color: #fff; margin-bottom: 32px;
  }}

  /* ── CARDS ── */
  .cards-grid {{ display: grid; gap: 14px; }}
  .cards-grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); }}
  .cards-grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }}
  .cards-grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}

  .card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 22px 20px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s, transform .2s;
  }}
  .card:hover {{
    border-color: rgba(99,179,237,0.3);
    transform: translateY(-2px);
  }}
  .card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent) 0%, transparent 70%);
  }}
  .card-icon {{ font-size: 22px; position: absolute; top: 18px; right: 18px; opacity: 0.22; }}
  .card-label {{
    font-size: 10px; font-weight: 600;
    color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 1.5px; margin-bottom: 10px;
  }}
  .card-value {{
    font-size: 26px; font-weight: 800; color: #fff; line-height: 1;
  }}
  .card-value.accent {{ color: var(--accent); }}
  .card-value.green  {{ color: var(--green); }}
  .card-value.yellow {{ color: var(--yellow); }}
  .card-value.red    {{ color: var(--red); }}
  .card-sub {{
    font-size: 11px; color: var(--text-muted); margin-top: 7px;
  }}

  /* ── DIVIDER ── */
  .divider {{
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,179,237,0.12), transparent);
    margin: 0;
  }}

  /* ── TABLE ── */
  .table-wrap {{
    overflow-x: auto;
    border-radius: 14px;
    border: 1px solid var(--card-border);
  }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); }}
  thead th {{
    padding: 13px 16px;
    font-size: 10px; font-weight: 700;
    color: var(--accent); text-transform: uppercase;
    letter-spacing: 1.2px; text-align: left;
    background: rgba(6,14,28,0.5);
    border-bottom: 1px solid rgba(99,179,237,0.12);
  }}
  tbody td {{
    padding: 12px 16px; font-size: 13px;
    color: var(--text-muted);
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  tbody tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover td {{ background: rgba(99,179,237,0.04); color: var(--text); }}
  .td-strong {{ font-weight: 700; color: #fff; }}

  /* ── BADGES ── */
  .status-badge {{
    display: inline-block; font-size: 10px; font-weight: 700;
    padding: 3px 10px; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .badge-ok   {{ background: rgba(72,187,120,0.12); color: var(--green); border: 1px solid rgba(72,187,120,0.28); }}
  .badge-opp  {{ background: rgba(236,201,75,0.12);  color: var(--yellow);border: 1px solid rgba(236,201,75,0.28); }}
  .badge-risk {{ background: rgba(252,129,129,0.12); color: var(--red);   border: 1px solid rgba(252,129,129,0.28); }}

  /* ── COMPARATIVO BANNER ── */
  .comp-banner {{
    background: var(--card-bg);
    border-radius: 12px; padding: 20px 22px;
    border-left: 3px solid var(--accent); margin-bottom: 24px;
  }}
  .comp-banner-title {{ font-size: 12px; font-weight: 700; color: var(--accent); margin-bottom: 5px; }}
  .comp-banner-text  {{ font-size: 13px; color: var(--text-muted); line-height: 1.7; }}
  .comp-banner-text strong {{ color: #fff; }}

  /* ── VARIAÇÕES ── */
  .var-up   {{ color: var(--green); font-weight: 700; }}
  .var-down {{ color: var(--red);   font-weight: 700; }}
  .var-flat {{ color: var(--text-muted); }}

  /* ── CHARTS ── */
  .charts-row {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 14px; margin: 24px 0;
  }}
  @media (max-width: 700px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
  .chart-card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px; padding: 22px;
    position: relative; overflow: hidden;
  }}
  .chart-card::before {{
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent) 0%, transparent 70%);
  }}
  .chart-card-label {{
    font-size: 10px; font-weight: 700;
    color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 1.5px; margin-bottom: 18px;
  }}

  /* ── FOOTER ── */
  footer {{
    background: var(--navy-900);
    border-top: 1px solid rgba(99,179,237,0.12);
    text-align: center; padding: 40px 24px 32px;
  }}
  .footer-brand {{ display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 10px; }}
  .footer-icon {{
    width: 30px; height: 30px;
    background: linear-gradient(135deg, var(--accent), #4299E1);
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 900; color: #fff;
  }}
  .footer-logo {{ font-size: 18px; font-weight: 900; color: #fff; }}
  .footer-logo span {{ color: var(--accent); }}
  .footer-sub  {{ font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 4px; }}
  .footer-line {{ width: 40px; height: 2px; background: linear-gradient(90deg, var(--accent), transparent); margin: 16px auto 12px; border-radius: 2px; }}

  @media (max-width: 600px) {{
    .hero {{ padding: 48px 20px 40px; }}
    .section {{ padding: 40px 0; }}
    .topbar {{ padding: 12px 20px; }}
    .hero-kpis {{ border-radius: 14px; }}
    .hero-kpi {{ min-width: 120px; padding: 16px 12px; }}
  }}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-icon">E</div>
    <div>
      <div class="topbar-name">Elevate <span>Ecom</span></div>
    </div>
  </div>
  <div class="topbar-tag">Relatório Semanal · Shopee</div>
</div>

<!-- HERO -->
<div class="hero">
  <div class="hero-eyebrow">Relatório de Performance</div>
  <div class="hero-client">{nome_cliente}</div>
  <h1>Últimos <em>7 dias</em></h1>
  <div class="hero-period">📅 {de} → {ate}</div>

  <div class="hero-kpis">
    <div class="hero-kpi">
      <div class="hero-kpi-label">Faturamento</div>
      <div class="hero-kpi-value">R$ {faturamento}</div>
    </div>
    <div class="hero-kpi">
      <div class="hero-kpi-label">Pedidos Pagos</div>
      <div class="hero-kpi-value">{total_pedidos}</div>
    </div>
    <div class="hero-kpi">
      <div class="hero-kpi-label">Invest. ADS</div>
      <div class="hero-kpi-value">R$ {investimento_ads}</div>
    </div>
    <div class="hero-kpi">
      <div class="hero-kpi-label">Receita ADS</div>
      <div class="hero-kpi-value">R$ {receita_ads}</div>
    </div>
    <div class="hero-kpi">
      <div class="hero-kpi-label">ROAS</div>
      <div class="hero-kpi-value">{roas}x</div>
    </div>
    <div class="hero-kpi">
      <div class="hero-kpi-label">TACOS</div>
      <div class="hero-kpi-value">{tacos}%</div>
    </div>
  </div>
</div>

<!-- MÉTRICAS PRINCIPAIS -->
<div class="section">
  <div class="container">
    <div class="section-label">Visão Geral</div>
    <div class="section-heading">Métricas Principais — {de} a {ate}</div>

    <div class="cards-grid cards-grid-4" style="margin-bottom:16px">
      <div class="card">
        <div class="card-icon">💰</div>
        <div class="card-label">Faturamento Bruto</div>
        <div class="card-value accent">R$ {faturamento}</div>
        <div class="card-sub">{total_pedidos} pedidos pagos</div>
      </div>
      <div class="card">
        <div class="card-icon">📢</div>
        <div class="card-label">Investimento ADS</div>
        <div class="card-value">R$ {investimento_ads}</div>
        <div class="card-sub">Total gasto em anúncios</div>
      </div>
      <div class="card">
        <div class="card-icon">📦</div>
        <div class="card-label">Receita via ADS</div>
        <div class="card-value accent">R$ {receita_ads}</div>
        <div class="card-sub">GMV atribuído ao ADS</div>
      </div>
      <div class="card">
        <div class="card-icon">🚀</div>
        <div class="card-label">ROAS</div>
        <div class="card-value {roas_color}">{roas}x</div>
        <div class="card-sub"><span class="status-badge {roas_badge_class}">{roas_badge_emoji} {roas_badge}</span></div>
      </div>
    </div>

    <div class="cards-grid cards-grid-3">
      <div class="card">
        <div class="card-icon">🎯</div>
        <div class="card-label">TACOS</div>
        <div class="card-value {tacos_color}">{tacos}%</div>
        <div class="card-sub"><span class="status-badge {tacos_badge_class}">{tacos_badge_emoji} {tacos_badge}</span></div>
      </div>
      <div class="card">
        <div class="card-icon">🛒</div>
        <div class="card-label">Qtd. Vendas via ADS</div>
        <div class="card-value accent">{quantidade_vendas_ads}</div>
        <div class="card-sub">Conversões atribuídas aos anúncios</div>
      </div>
      <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-label">Receita Orgânica</div>
        <div class="card-value green">R$ {receita_organica}</div>
        <div class="card-sub">Faturamento fora do ADS</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-card-label">Faturamento vs Receita ADS</div>
        <canvas id="chartBar" height="200"></canvas>
      </div>
      <div class="chart-card">
        <div class="chart-card-label">Composição do Faturamento</div>
        <canvas id="chartDoughnut" height="200"></canvas>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Métrica</th><th>Valor</th><th>Descrição</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td>Faturamento Bruto</td><td class="td-strong">R$ {faturamento}</td><td>Total de pedidos pagos no período</td><td><span class="status-badge badge-ok">🟢 OK</span></td></tr>
          <tr><td>Pedidos Pagos</td><td class="td-strong">{total_pedidos}</td><td>Pedidos com pagamento confirmado</td><td><span class="status-badge badge-ok">🟢 OK</span></td></tr>
          <tr><td>Investimento ADS</td><td class="td-strong">R$ {investimento_ads}</td><td>Total gasto em anúncios patrocinados</td><td><span class="status-badge badge-opp">🟡 Oportunidade</span></td></tr>
          <tr><td>Receita via ADS</td><td class="td-strong">R$ {receita_ads}</td><td>Faturamento gerado pelos anúncios</td><td><span class="status-badge badge-ok">🟢 OK</span></td></tr>
          <tr><td>ROAS</td><td class="td-strong">{roas}x</td><td>Para cada R$1 investido, retornou R${roas} em receita</td><td><span class="status-badge {roas_badge_class}">{roas_badge_emoji} {roas_badge}</span></td></tr>
          <tr><td>TACOS</td><td class="td-strong">{tacos}%</td><td>% do investimento ADS sobre o faturamento total</td><td><span class="status-badge {tacos_badge_class}">{tacos_badge_emoji} {tacos_badge}</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- FOOTER -->
<footer>
  <div class="footer-brand">
    <div class="footer-icon">E</div>
    <div class="footer-logo">Elevate <span>Ecom</span></div>
  </div>
  <div class="footer-line"></div>
  <div class="footer-sub">Relatório gerado por Elevate Ecom &nbsp;·&nbsp; {nome_cliente} &nbsp;·&nbsp; {de} → {ate}</div>
  <div style="margin-top:6px; font-size:10px; color:rgba(255,255,255,0.18);">Gerado em {gerado_em} &nbsp;·&nbsp; Dados extraídos do painel Shopee Brasil</div>
</footer>

<script>
  Chart.defaults.color = 'rgba(255,255,255,0.4)';
  Chart.defaults.borderColor = 'rgba(126,200,227,0.08)';
  Chart.defaults.font.family = 'Poppins';

  new Chart(document.getElementById('chartBar'), {{
    type: 'bar',
    data: {{
      labels: ['Faturamento Total', 'Receita via ADS'],
      datasets: [{{
        data: [{faturamento_raw}, {receita_ads_raw}],
        backgroundColor: ['#7EC8E3', '#4ade80'],
        borderRadius: 8, borderSkipped: false
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ grid: {{ color: 'rgba(126,200,227,0.06)' }} }},
        y: {{ beginAtZero: true, grid: {{ color: 'rgba(126,200,227,0.06)' }},
              ticks: {{ callback: v => 'R$' + v.toLocaleString('pt-BR') }} }}
      }}
    }}
  }});

  const recOrg = Math.max(0, {faturamento_raw} - {receita_ads_raw});
  new Chart(document.getElementById('chartDoughnut'), {{
    type: 'doughnut',
    data: {{
      labels: ['Receita Orgânica', 'Receita via ADS'],
      datasets: [{{
        data: [recOrg, {receita_ads_raw}],
        backgroundColor: ['#7EC8E3', '#4ade80'],
        hoverOffset: 8, borderWidth: 0
      }}]
    }},
    options: {{
      responsive: true, cutout: '65%',
      plugins: {{
        legend: {{ position: 'bottom' }},
        tooltip: {{ callbacks: {{ label: ctx => ' R$ ' + ctx.parsed.toLocaleString('pt-BR') }} }}
      }}
    }}
  }});

</script>
</body>
</html>
"""


def _badge(metric: str, value: float) -> tuple[str, str, str, str]:
    """Retorna (classe_css, texto, emoji, cor_card)."""
    if metric == "roas":
        if value >= 5:  return "badge-ok",   "OK",           "🟢", "green"
        if value >= 2:  return "badge-opp",  "Oportunidade", "🟡", "yellow"
        return "badge-risk", "Risco", "🔴", "red"
    if metric == "tacos":
        if value <= 10: return "badge-ok",   "OK",           "🟢", "green"
        if value <= 25: return "badge-opp",  "Oportunidade", "🟡", "yellow"
        return "badge-risk", "Risco", "🔴", "red"
    return "badge-opp", "Oportunidade", "🟡", "yellow"


def _fmt_brl(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _var_html(var: float | None, inverso: bool = False) -> str:
    if var is None:
        return '<span class="var-flat">— sem dado anterior</span>'
    if var == 0:
        return '<span class="var-flat">→ 0,0%</span>'
    subiu = var > 0
    bom   = subiu if not inverso else not subiu
    css   = "var-up" if bom else "var-down"
    seta  = "▲" if subiu else "▼"
    return f'<span class="{css}">{seta} {abs(var):.1f}%</span>'


def gerar_relatorio(dados: dict, output_dir: str = "reports") -> str:
    os.makedirs(output_dir, exist_ok=True)

    periodo      = dados["periodo"]
    prev         = dados.get("periodo_anterior", {"de": "—", "ate": "—"})
    nome_cliente = dados.get("nome_cliente", "")
    fat          = dados["faturamento"]
    ped      = dados["total_pedidos"]
    inv      = dados["investimento_ads"]
    rec      = dados["receita_ads"]
    roas     = dados["roas"]
    tacos    = dados["tacos"]
    qtd_ads  = dados.get("quantidade_vendas_ads", 0)

    fat_prev   = dados.get("faturamento_prev",      0.0)
    ped_prev   = dados.get("pedidos_prev",           0)
    inv_prev   = dados.get("investimento_ads_prev",  0.0)
    rec_prev   = dados.get("receita_ads_prev",       0.0)
    roas_prev  = dados.get("roas_prev",              0.0)
    tacos_prev = dados.get("tacos_prev",             0.0)

    rec_org = max(0.0, fat - rec)

    roas_bc,  roas_bt,  roas_em,  roas_col  = _badge("roas",  roas)
    tacos_bc, tacos_bt, tacos_em, tacos_col = _badge("tacos", tacos)

    html = HTML_TEMPLATE.format(
        nome_cliente    = nome_cliente,
        de              = periodo["de"],
        ate             = periodo["ate"],
        prev_de         = prev["de"],
        prev_ate        = prev["ate"],
        gerado_em       = datetime.now().strftime("%d/%m/%Y %H:%M"),

        faturamento          = _fmt_brl(fat),
        faturamento_raw      = fat,
        total_pedidos        = ped,
        investimento_ads     = _fmt_brl(inv),
        investimento_ads_raw = inv,
        receita_ads          = _fmt_brl(rec),
        receita_ads_raw      = rec,
        receita_organica     = _fmt_brl(rec_org),
        roas                 = f"{roas:.2f}",
        tacos                = f"{tacos:.2f}",
        quantidade_vendas_ads= qtd_ads,

        roas_badge_class  = roas_bc,
        roas_badge        = roas_bt,
        roas_badge_emoji  = roas_em,
        roas_color        = roas_col,
        tacos_badge_class = tacos_bc,
        tacos_badge       = tacos_bt,
        tacos_badge_emoji = tacos_em,
        tacos_color       = tacos_col,

    )

    filename = (
        f"relatorio_shopee_"
        f"{periodo['de'].replace('/', '-')}_a_"
        f"{periodo['ate'].replace('/', '-')}.html"
    )
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Relatório] Dashboard salvo em: {filepath}")
    return filepath
