from app import DEXExchange
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    config = {
        'rpcUrl': f"https://mainnet.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}",
        'privateKey': os.getenv('PRIVATE_KEY'),
        'poa': False
    }
    
    dex = DEXExchange(config)
    
    # Test with Vitalik's wallet (has tokens)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    print(f"Testing with address: {test_address}")
    
    # Test each token individually
    for symbol, address in dex.common_tokens.items():
        try:
            position = dex.get_token_position(test_address, address)
            if position['balance'] > 0:
                print(f"{symbol}: {position['balance']}")
        except Exception as e:
            print(f"Error with {symbol}: {e}")

if __name__ == "__main__":
    main()