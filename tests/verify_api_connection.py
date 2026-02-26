import os
import time
import hmac
import hashlib
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def load_env_local(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env[key] = value
    return env

def verify_binance():
    # 1. Load Keys
    env_path = '/home/jkpark/.openclaw/workspace-jeff/bats-trading-system/.env.local'
    env = load_env_local(env_path)
    api_key = env.get('BINANCE_API_KEY')
    api_secret = env.get('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        print("❌ Error: API Key or Secret not found in .env.local")
        return

    print(f"Checking API Key: {api_key[:6]}...{api_key[-4:]}")

    # 2. Prepare Request (Testnet first)
    # Note: Testnet keys only work on testnet, Mainnet keys only on mainnet.
    # We will try both if one fails.
    
    endpoints = [
        ("Spot Testnet", "https://testnet.binance.vision"),
        ("Mainnet", "https://api.binance.com")
    ]

    for name, base_url in endpoints:
        print(f"\n--- Testing on {name} ---")
        timestamp = int(time.time() * 1000)
        params = {'timestamp': timestamp}
        query_string = urlencode(params)
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        url = f"{base_url}/api/v3/account?{query_string}&signature={signature}"
        
        req = Request(url)
        req.add_header('X-MBX-APIKEY', api_key)
        
        try:
            with urlopen(req) as response:
                res_data = json.loads(response.read().decode())
                print(f"✅ Success! Connected to {name}.")
                print(f"Account Permissions: {res_data.get('permissions')}")
                # Show small part of balance
                balances = [b for b in res_data.get('balances', []) if float(b['free']) > 0 or float(b['locked']) > 0]
                print(f"Active Balances: {balances[:3]}...")
                return # Stop if one succeeds
        except Exception as e:
            print(f"❌ Failed on {name}: {e}")

if __name__ == "__main__":
    verify_binance()
