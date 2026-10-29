import requests

API_KEY = "sk-FAKEFAKEFAKEFAKEFAKE1234"
BASE = "https://api.example.com/v1"


def get_prices(symbol):
    """Fetch the latest price for a symbol."""
    r = requests.get(f"{BASE}/price/{symbol}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
    r.raise_for_status()
    return r.json()["price"]


def watchlist(symbols):
    """Fetch prices for many symbols."""
    return {s: get_prices(s) for s in symbols}


if __name__ == "__main__":
    print(watchlist(["AAA", "BBB"]))
