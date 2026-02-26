import os

def load_env_local_manual(path):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def test_manual_load():
    path = '/home/jkpark/.openclaw/workspace-jeff/bats-trading-system/.env.local'
    load_env_local_manual(path)
    key = os.getenv('BINANCE_API_KEY')
    print(f"Loaded key: {key}")
    if key == 'your_api_key_here':
        print("SUCCESS")
    else:
        print("FAILED")

if __name__ == "__main__":
    test_manual_load()
