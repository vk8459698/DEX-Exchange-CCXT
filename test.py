from app import DEXExchange
import os
from dotenv import load_dotenv

load_dotenv()

def test_approvals():
    dex = DEXExchange({
        'rpcUrl': f"https://mainnet.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}",
        'privateKey': os.getenv('PRIVATE_KEY'),
    })
    
    # Test with different addresses that likely have approvals
    test_addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",  # Uniswap LP
        "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503",  # Active DeFi user
    ]
    
    for address in test_addresses:
        print(f"\n=== Testing Address: {address[:10]}... ===")
        
        # Check positions
        print("Positions:")
        dex.address = address
        try:
            balance = dex.fetch_balance()
            count = 0
            for token, bal in balance.items():
                if bal['free'] > 0:
                    print(f"  {token}: {bal['free']:,.6f}")
                    count += 1
                if count >= 3:  # Limit output
                    break
            if count == 0:
                print("  No tokens found")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check approvals for USDC
        print("USDC Approvals:")
        try:
            usdc_addr = dex.common_tokens['USDC']
            approvals = dex.fetch_approvals(usdc_addr)
            found_approvals = False
            for approval in approvals:
                if approval['allowance'] > 0:
                    spender = approval.get('spender_name', 'Unknown')
                    amount = "UNLIMITED" if approval['is_unlimited'] else f"{approval['allowance']:,.2f}"
                    print(f"  {spender}: {amount}")
                    found_approvals = True
            if not found_approvals:
                print("  No active approvals")
        except Exception as e:
            print(f"  Error: {e}")

def test_manual_approval_check():
    """Test approval checking with known contract addresses"""
    dex = DEXExchange({
        'rpcUrl': f"https://mainnet.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}",
    })
    
    print("\n=== MANUAL APPROVAL TEST ===")
    
    # Check a specific approval (Vitalik's USDC approval to Uniswap V2)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    usdc_addr = dex.common_tokens['USDC']
    uniswap_router = dex.contracts['uniswap_v2_router']
    
    try:
        approval = dex.get_token_approval(test_address, usdc_addr, uniswap_router)
        print(f"USDC approval to Uniswap V2:")
        print(f"  Amount: {approval['allowance']:,.6f}")
        print(f"  Unlimited: {approval['is_unlimited']}")
        print(f"  Raw: {approval['raw_allowance']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_approvals()
    test_manual_approval_check()