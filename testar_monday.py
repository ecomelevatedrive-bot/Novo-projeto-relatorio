import requests, json

TOKEN    = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjY1NjA0MDQ1NSwiYWFpIjoxMSwidWlkIjo4NDIwMDIwMCwiaWFkIjoiMjAyNi0wNS0wOFQyMTozMzo0Mi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjcxNTYyNTEsInJnbiI6InVzZTEifQ.R8Sjc4kt0UZgbIlMuF1npP3OAhVHrgDiK-_6pdnjlao"
BOARD_ID = "18414132966"

headers = {
    "Authorization": TOKEN,
    "Content-Type":  "application/json",
    "API-Version":   "2023-10",
}

# 1. Verifica se o board existe e lista grupos
print("=== Testando board", BOARD_ID, "===")
query = """
query ($bid: ID!) {
  boards(ids: [$bid]) {
    id name
    groups { id title }
  }
}
"""
resp = requests.post("https://api.monday.com/v2",
                     json={"query": query, "variables": {"bid": BOARD_ID}},
                     headers=headers, timeout=30)
print("Status HTTP:", resp.status_code)
data = resp.json()
print(json.dumps(data, indent=2, ensure_ascii=False))

# 2. Tenta criar um grupo de teste
if data.get("data", {}).get("boards"):
    board = data["data"]["boards"][0]
    print(f"\nBoard encontrado: '{board['name']}' — {len(board['groups'])} grupos")

    print("\n=== Criando grupo de teste ===")
    mut = """
    mutation ($bid: ID!, $name: String!) {
      create_group(board_id: $bid, group_name: $name) { id }
    }
    """
    resp2 = requests.post("https://api.monday.com/v2",
                          json={"query": mut, "variables": {"bid": BOARD_ID, "name": "TESTE_SCRIPT"}},
                          headers=headers, timeout=30)
    print("Status HTTP:", resp2.status_code)
    print(json.dumps(resp2.json(), indent=2, ensure_ascii=False))
else:
    print("\n⚠ Board NÃO encontrado ou sem acesso!")
