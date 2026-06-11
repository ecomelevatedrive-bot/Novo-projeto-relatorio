# ============================================================
#  CONFIGURAÇÕES DA API SHOPEE
#  Preencha com suas credenciais do Shopee Open Platform
#  https://open.shopee.com/
# ============================================================

PARTNER_ID     = 0          # Seu Partner ID (inteiro)
PARTNER_KEY    = ""         # Sua Partner Key (string)
SHOP_ID        = 0          # ID da sua loja (inteiro)
ACCESS_TOKEN   = ""         # Access Token da loja

# Ambiente: "production" ou "sandbox"
ENVIRONMENT = "production"

# ============================================================
#  CONFIGURAÇÕES DO MONDAY.COM
# ============================================================

MONDAY_API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjY1NjA0MDQ1NSwiYWFpIjoxMSwidWlkIjo4NDIwMDIwMCwiaWFkIjoiMjAyNi0wNS0wOFQyMTozMzo0Mi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjcxNTYyNTEsInJnbiI6InVzZTEifQ.R8Sjc4kt0UZgbIlMuF1npP3OAhVHrgDiK-_6pdnjlao"

# Board: "Relatorios / Rafael / Gustavo" — nhubecom.monday.com/boards/18414132966
# NAO ALTERAR: 18410901694 e o board "Ezequiel - Execucao" (tarefas), NAO de relatorios.
MONDAY_BOARD_ID  = "18414132966"

# ============================================================
#  CONFIGURAÇÕES DO DOLPHIN ANTY
# ============================================================

DOLPHIN_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZWYyMzY2OGYzMmQ4MDBjYjg1ZWUzYzc3MmJkMDhjNGQ4YWQ4YTNjN2RiNGZiYjMxZTg3ZmQ2M2YxZTE2YzI5YTNjYWQxYmFjNTQwNjJkODEiLCJpYXQiOjE3Nzg5MzQ2NTAuMDMwMjg2LCJuYmYiOjE3Nzg5MzQ2NTAuMDMwMjkxLCJleHAiOjE4MTA0NzA2NTAuMDE3MDE1LCJzdWIiOiI1MDM1MjY3Iiwic2NvcGVzIjpbXSwidGVhbV9pZCI6NDkzMzMwNCwidGVhbV9wbGFuIjoidGVhbSIsInRlYW1fcGxhbl9leHBpcmF0aW9uIjoxNzgxMDk5ODExfQ.IQemvyh0K8Qvwt6QA_JgOHZibr9JePxu2_7CdCbjR0-j-L_dG_CY0nQWaJx1RHKuCj_aG8s9JGThtnzJOaj3IgUBT6f9PCM8okcMojjFmF9K66Dp1KtpGTYsYj6w8PyA90QxJ_Szlhwaa5uj1ryLNCUQ7UmIUS9lkLdua4Hcv5l1dnnh16Fbwrl0ehaK6GF_ZS1Np5mhtO6uUT4H7TCQc7xWEELmy7IWh8n-CO-WF-552iiit3-jxi2lMV7AMc91xgIi7D-wnrlGtXsgzAMKHbPJarC0MaC3F66tpq0HU0r1DHEo6V5V9SdVRjeQDUjauJL0lfZK1ViAxmv6jtIicNt7-1Ud50o4bgytUa4mrGGNTnT5lpmGdXtG5vcKFRjNd6iXvGUPkD3O_4k-KolnzNwPNZdL2zQgZIpYFvJZ9K2aDj8jSWfB_WyljQmut9nH_xY0dY7Rf-dl9KFVHrifb7z6KuK80cS1f83_m8m88bFcAIwx65oy2cD3fp8aw2tTkYbkFLtxzGNfZHrFNE89lZmEU1Um9Cxul87MMlyLKIcMNl7hkhowP8XVwVrcFJaHQP_N6PYNdZDqalZX0nGHF2S8T99O80XgCY-Mh2h0XIixaeJJ0fYc1plubBBAMoKP3PJJnJ1usD0a3a_Hl4G8vIlbeu5k85o4mG4cRRp_jHo"

BASE_URLS = {
    "production": "https://partner.shopeemobile.com",
    "sandbox":    "https://partner.uat.shopeemobile.com",
}

BASE_URL = BASE_URLS[ENVIRONMENT]
