import os
from dotenv import load_dotenv

def test_dotenv_local():
    # Clear existing env vars to be sure
    if 'BINANCE_API_KEY' in os.environ: del os.environ['BINANCE_API_KEY']
    
    # Load .env.local
    load_dotenv('.env.local')
    
    key = os.getenv('BINANCE_API_KEY')
    print(f"Loaded key from .env.local: {key}")
    
    if key == 'your_api_key_here':
        print("TEST SUCCESS: .env.local loaded correctly.")
        return True
    else:
        print("TEST FAILED: .env.local not loaded.")
        return False

if __name__ == "__main__":
    test_dotenv_local()
