@echo off
chcp 65001 >nul
title Preview do Design HTML

cd /d "%~dp0"

echo.
echo =====================================================
echo   PREVIEW DO DESIGN HTML
echo =====================================================
echo.

"C:\Users\User\AppData\Local\Python\bin\python.exe" -c "
from report_generator import gerar_relatorio
dados = {
    'nome_cliente': 'Foreli',
    'periodo': {'de': '13/05/2025', 'ate': '19/05/2025'},
    'periodo_anterior': {'de': '06/05/2025', 'ate': '12/05/2025'},
    'faturamento': 12500.00, 'total_pedidos': 87,
    'investimento_ads': 980.00, 'receita_ads': 5200.00,
    'roas': 5.31, 'tacos': 7.84, 'quantidade_vendas_ads': 42,
    'faturamento_prev': 10800.00, 'pedidos_prev': 74,
    'investimento_ads_prev': 850.00, 'receita_ads_prev': 4300.00,
    'roas_prev': 5.06, 'tacos_prev': 7.87,
    'var_faturamento': 15.7, 'var_pedidos': 17.6,
    'var_investimento': 15.3, 'var_receita_ads': 20.9,
    'var_roas': 4.9, 'var_tacos': -0.3,
}
path = gerar_relatorio(dados, output_dir='reports/PREVIEW')
print('Arquivo gerado:', path)
import os, subprocess
subprocess.Popen(['start', '', path], shell=True)
"

echo.
echo =====================================================
echo   Pressione qualquer tecla para fechar...
echo =====================================================
pause >nul
